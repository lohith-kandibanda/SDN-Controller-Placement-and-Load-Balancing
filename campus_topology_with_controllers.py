from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

def campus_network_topology():
    net = Mininet(switch=OVSSwitch, link=TCLink)

    # Add controllers based on the controller placement output
    c1 = net.addController('c1', controller=RemoteController, ip='127.0.0.1', port=6633)  # Controller for dist1
    c2 = net.addController('c2', controller=RemoteController, ip='127.0.0.1', port=6634)  # Controller for dist3

    # Add switches
    core1 = net.addSwitch('core1')
    core2 = net.addSwitch('core2')

    dist1 = net.addSwitch('dist1')
    dist2 = net.addSwitch('dist2')
    dist3 = net.addSwitch('dist3')
    dist4 = net.addSwitch('dist4')

    acc1 = net.addSwitch('acc1')
    acc2 = net.addSwitch('acc2')
    acc3 = net.addSwitch('acc3')
    acc4 = net.addSwitch('acc4')

    # Add hosts
    h1 = net.addHost('h1', ip='10.0.1.1')
    h2 = net.addHost('h2', ip='10.0.1.2')
    h3 = net.addHost('h3', ip='10.0.2.1')
    h4 = net.addHost('h4', ip='10.0.2.2')
    h5 = net.addHost('h5', ip='10.0.3.1')
    h6 = net.addHost('h6', ip='10.0.3.2')
    h7 = net.addHost('h7', ip='10.0.4.1')
    h8 = net.addHost('h8', ip='10.0.4.2')

    # Add links
    net.addLink(acc1, h1)
    net.addLink(acc1, h2)
    net.addLink(acc2, h3)
    net.addLink(acc2, h4)
    net.addLink(acc3, h5)
    net.addLink(acc3, h6)
    net.addLink(acc4, h7)
    net.addLink(acc4, h8)

    net.addLink(acc1, dist1)
    net.addLink(acc2, dist2)
    net.addLink(acc3, dist3)
    net.addLink(acc4, dist4)

    net.addLink(dist1, core1)
    net.addLink(dist2, core1)
    net.addLink(dist3, core2)
    net.addLink(dist4, core2)

    net.addLink(core1, core2)

    # Set switches to standalone mode
    switches = [core1, core2, dist1, dist2, dist3, dist4, acc1, acc2, acc3, acc4]
    for switch in switches:
        switch.cmd('ovs-vsctl set-fail-mode {} standalone'.format(switch.name))

    # Manually bind controllers to the selected switches (dist1 and dist3)
    for switch, controller in [(dist1, 'tcp:127.0.0.1:6633'), 
                                (dist3, 'tcp:127.0.0.1:6634')]:
        switch.cmd('ovs-vsctl set-controller {} {}'.format(switch.name, controller))

    # Remove redundant controllers from other switches
    for switch in [dist2, dist4, core1, core2, acc1, acc2, acc3, acc4]:
        switch.cmd('ovs-vsctl del-controller {}'.format(switch.name))

    # Start the network
    net.start()

    # Test connectivity
    print("\nTesting network connectivity...")
    net.pingAll()

    # Start CLI for interactive testing
    CLI(net)

    # Stop the network
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    campus_network_topology()

