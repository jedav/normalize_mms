#!/usr/bin/env python2

import xml.etree.ElementTree as ET
import re
import sys

# regular expression for finding things that look like international phone numbers
# developed from a handful of examples rather than the RFCs, so...  works generally, could miss edge cases
PHONE_RE = re.compile(r"^(?:00[ -]?|\+?)(\d{0,3}?)[ -]?\(?(\d{3})\)?[ -]?(\d{3})[ -]?(\d{4})$")
# names of groups extracted by regex, by position
RE_PARTS = ["country", "area", "first", "last"]

# XML XPATH expression for finding nodes that have "address" attributes
ADDR_XPATH = ".//*[@address]"

class AddrData(object):
  def __init__(self, addrdict):
    self.canon = addrdict["first"]+addrdict["last"]
    self.area = addrdict["area"]
    if not len(self.area):
      self.area = None
    self.country = addrdict["country"]
    if not len(self.country):
      self.country = None

  def update(self, other):
    assert self.canon == other.canon
    if other.country is not None:
      if self.country is None:
        self.country = other.country
      assert self.country == other.country
    if other.area is not None:
      if self.area is None:
        self.area = other.area
      assert self.area == other.area

  def __str__(self):
    out = ""
    if self.country:
      out += "+"+self.country
    if self.area:
      out += self.area
    out += self.canon
    return out


# functions for gathering addresses

def add_addr(addrmap, addr):
  match = PHONE_RE.match(addr)
  if match is None:
    return
  parts = dict(zip(RE_PARTS, match.groups()))
  canon = parts["first"] + parts["last"]
  if canon in addrmap:
    new_addr = AddrData(parts)
    addrmap[canon].update(new_addr)
  else:
    addrmap[canon] = AddrData(parts)
  
def gather_addrs(root):
  # here we look for multiple versions of the same address, some of which might have more information than others
  # to make sure that when we canonicalize addresses, we do so correctly
  # (rather than assuming, eg, that all addresses with unspecified country codes are USA)
  addrmap = {}
  addrs = [e.get("address") for e in root.findall(ADDR_XPATH)]
  for addr in addrs:
    if '~' in addr:
      parts = addr.split('~')
      for part in parts:
        add_addr(addrmap, part)
    else:
      add_addr(addrmap, addr)
  return addrmap

# functions for outputting normalized addresses

def normalize_addr(addrmap, addr):
  match = PHONE_RE.match(addr)
  if match is None:
    return addr
  parts = dict(zip(RE_PARTS, match.groups()))
  canon = parts["first"] + parts["last"]
  assert canon in addrmap
  return str(addrmap[canon])
  
def update_addrs(root, addrmap):
  nodes = root.findall(ADDR_XPATH)
  for node in nodes:
    address = node.get("address")
    if '~' in address:
      addresses = address.split('~')
    else:
      addresses = [address]
    addresses = [normalize_addr(addrmap, addr) for addr in addresses]
    address = '~'.join(addresses)
    node.set("address", address)


def parse_args():
  if len(sys.argv) < 2:
    print "USAGE: %s path/to/input/db.xml [path/to/output/db.xml]"%sys.argv[0]
    sys.exit(-1)
  inpath = sys.argv[1]
  if len(sys.argv) >= 3:
    outpath = sys.argv[2]
  else:
    inpath_parts = inpath.split('.')
    inpath_suffix = inpath_parts[-1]
    inpath_prefix = '.'.join(inpath_parts[:-1])
    outpath = inpath_prefix+"-compressed."+inpath_suffix
  return (inpath, outpath)


def main():
  (inpath, outpath) = parse_args()
  tree = ET.parse(inpath)
  root = tree.getroot()
  addrmap = gather_addrs(root)
  update_addrs(root, addrmap)
  tree.write(outpath)


if __name__ == "__main__":
  main()

