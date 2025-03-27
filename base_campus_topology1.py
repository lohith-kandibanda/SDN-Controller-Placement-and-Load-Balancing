from mininet.net import Mininet
from mininet.node import OVSSwitch, Controller
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

def base_campus_network_topology_with_default_controllers():
    # Initialize Mininet with OVSSwitch and TCLink
    net = Mininet(switch=OVSSwitch, link=TCLink)

    # Add two default controllers
    c1 = net.addController('c1')  # Default Mininet controller
    c2 = net.addController('c2')  # Another default Mininet controller

    # Add core switches
    core1 = net.addSwitch('core1')
    core2 = net.addSwitch('core2')

    # Add distribution switches
    dist1 = net.addSwitch('dist1')  # Normal switch
    dist2 = net.addSwitch('dist2')  # Normal switch
    dist3 = net.addSwitch('dist3')  # Normal switch
    dist4 = net.addSwitch('dist4')  # Normal switch

    # Add access switches
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

    # Add links between hosts and access switches
    net.addLink(acc1, h1)
    net.addLink(acc1, h2)
    net.addLink(acc2, h3)
    net.addLink(acc2, h4)
    net.addLink(acc3, h5)
    net.addLink(acc3, h6)
    net.addLink(acc4, h7)
    net.addLink(acc4, h8)

    # Add links between access switches and distribution switches
    net.addLink(acc1, dist1)
    net.addLink(acc2, dist2)
    net.addLink(acc3, dist3)
    net.addLink(acc4, dist4)

    # Add links between distribution switches and core switches
    net.addLink(dist1, core1)
    net.addLink(dist2, core1)
    net.addLink(dist3, core2)
    net.addLink(dist4, core2)

    # Add link between core switches
    net.addLink(core1, core2)

    # Start the network
    net.start()

    # Test connectivity between all hosts
    print("\nTesting network connectivity...")
    net.pingAll()

    # Start CLI for interactive testing
    CLI(net)

    # Stop the network
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    base_campus_network_topology_with_default_controllers()

