#! /usr/bin/python
import os, commands, sys, getopt


def usage():
    print ""
    print "bondServer -i <IP>  -m <MASK> -g <GATEWAY>"
    print ""

def get_ifs_list():
    cmd = "ip link | grep BROADCAST"
    output = commands.getoutput(cmd)
    output = output.split("\n")
    list_of_nic = []
    for o in output:
        devname = o.split(':')[1].strip()
        if devname == "lo":
            continue
        if devname == "virbr0":
            continue
        if devname == 'zt0':
            continue
        if devname == "bond0":
            exit()
        list_of_nic.append(devname)

    return list_of_nic

def gen_network_interfaces_bond_part(msg, get_ifs_list):
    bond0_template_1 = '''
auto bond0
iface bond0 inet static
address %s
netmask %s
gateway %s'''
    bond0_template_2 = '''
up ifenslave bond0 %s
down ifenslave -d bond0 %s
'''

    part1 = bond0_template_1 % (msg['ip'], msg['mask'], msg['gateway'])
    part2_var = ''
    for i in get_ifs_list:
        part2_var += (i + " ")
    part2 = bond0_template_2 % (part2_var, part2_var)

    return part1 + part2

def gen_network_interfaces_nic_part(nics):
    output = ""
    bond_if_template = '''
auto %s
iface %s inet dhcp
    '''
    ifs = ['lo'] + nics
    for i in ifs:
        tmp_str = bond_if_template % (i, i)
        output = output + tmp_str
    return output

def install_ifenslave():
    cmd = "apt-get install ifenslave"
    #commands.getoutput(cmd)

def configure_mode6_bonding():
    cmd = 'echo "bonding mode=6 miimon=100" >> /etc/modules'
    #commands.getoutput(cmd)

def main(argv):
    if len(argv) == 0:
        usage()
        return

    message = {}
    try:
      opts, args = getopt.getopt(argv,"i:m:g:")
      for opt, arg in opts:
          if opt in ( "-i"):
             message['ip'] =  arg
          if opt in ("-m"):
             message['mask'] = arg
          if opt in ("-g"):
             message['gateway'] = arg
    except getopt.GetoptError:
        usage()
        return

    nics = get_ifs_list()
    install_ifenslave()
    configure_mode6_bonding()
    configfile = gen_network_interfaces_nic_part(nics) + gen_network_interfaces_bond_part(message, nics)
    print configfile

if __name__ == '__main__':
    main(sys.argv[1:])
