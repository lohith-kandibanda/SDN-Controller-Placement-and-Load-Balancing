from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4


class DynamicWeightedLoadBalancer(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DynamicWeightedLoadBalancer, self).__init__(*args, **kwargs)
        self.server_pool = ['10.0.0.2', '10.0.0.3', '10.0.0.4']  # Server IPs
        self.server_weights = [3, 2, 1]  # Weights for each server
        self.round_robin_index = 0

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Install table-miss flow entry and proactive flow entries."""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

        # Proactively install flow rules for server-client traffic
        self.add_proactive_rules(datapath)

    def add_flow(self, datapath, priority, match, actions, idle_timeout=0, hard_timeout=0):
        """Add a flow entry to the switch."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        instructions = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        flow_mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                     match=match, instructions=instructions,
                                     idle_timeout=idle_timeout, hard_timeout=hard_timeout)
        datapath.send_msg(flow_mod)

    def add_proactive_rules(self, datapath):
        """Proactively add flow rules to reduce PACKET_IN messages."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install flows for traffic from clients to servers
        for server_ip in self.server_pool:
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst=server_ip)
            actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
            self.add_flow(datapath, 10, match, actions)

        # Install flows for traffic from servers to clients
        for server_ip in self.server_pool:
            match = parser.OFPMatch(eth_type=0x0800, ipv4_src=server_ip)
            actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
            self.add_flow(datapath, 10, match, actions)

        # Install a default flow to forward unmatched traffic
        default_match = parser.OFPMatch()
        default_actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
        self.add_flow(datapath, 0, default_match, default_actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Handle incoming packets."""
        msg = ev.msg
        datapath = msg.datapath
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # Ignore LLDP packets
        if eth.ethertype == 0x88cc:
            return

        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if ip_pkt:
            self.logger.info(f"Packet In: {ip_pkt.src} -> {ip_pkt.dst}")
            if ip_pkt.dst in self.server_pool:
                selected_server = self.select_server(ip_pkt.src)
                self.logger.info(f"Redirecting traffic to server {selected_server}")
                self.rewrite_packet(ip_pkt, selected_server, datapath, in_port, msg)
                return

        # Default behavior: Flood for unknown packets
        out_port = datapath.ofproto.OFPP_FLOOD
        actions = [parser.OFPActionOutput(out_port)]
        data = msg.data if msg.buffer_id == datapath.ofproto.OFP_NO_BUFFER else None
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def select_server(self, client_ip):
        """Select a server based on dynamic weighted round-robin."""
        total_weight = sum(self.server_weights)
        self.round_robin_index = (self.round_robin_index + 1) % total_weight
        running_sum = 0

        for i, weight in enumerate(self.server_weights):
            running_sum += weight
            if self.round_robin_index < running_sum:
                return self.server_pool[i]

    def rewrite_packet(self, ip_pkt, selected_server, datapath, in_port, msg):
        """Rewrite the packet to redirect it to the selected server."""
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Forward path: Client -> Server
        forward_actions = [parser.OFPActionSetField(ipv4_dst=selected_server),
                           parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
        forward_match = parser.OFPMatch(in_port=in_port,
                                        eth_type=0x0800,
                                        ipv4_src=ip_pkt.src,
                                        ipv4_dst=ip_pkt.dst)
        self.add_flow(datapath, 20, forward_match, forward_actions)

        # Reverse path: Server -> Client
        reverse_actions = [parser.OFPActionSetField(ipv4_src=ip_pkt.dst),
                           parser.OFPActionOutput(in_port)]
        reverse_match = parser.OFPMatch(eth_type=0x0800,
                                        ipv4_src=selected_server,
                                        ipv4_dst=ip_pkt.src)
        self.add_flow(datapath, 20, reverse_match, reverse_actions)

        # Send the packet out
        data = msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=forward_actions, data=data)
        datapath.send_msg(out)

