import urllib
import urllib2
import json
import os
import re

def req(method, args={}):
  base = 'http://api.glitch.com/simple/'
  result = urllib2.urlopen('%s%s?%s' % (base, method, urllib.urlencode(args)))
  return json.load(result)
  
def store(method, args, result):
  args_encoded = urllib.urlencode(args)
  open('%s#%s' % (method, args_encoded), 'w').write(json.dumps(result))
  
def load(method, args):
  args_encoded = urllib.urlencode(args)
  filename = '%s#%s' % (method, args_encoded)
  if not os.path.exists(filename):
    return None
  return json.load(open(filename))
  
def load_or_req(method, args={}):
  result = load(method, args)
  if not result:
    result = req(method, args)
    if result and result['ok']:
      store(method, args, result)
    
  return result
  
###

def extract_features(street_info):
  FEATURE_RE = re.compile('<b>(.*?)</b>')
  COUNT_RE = re.compile('^(\d+) (.*)$')
  features_list = street_info['features']
  features = []
  for feature_string in features_list:
    features += FEATURE_RE.findall(feature_string)
    
  feature_counts = []
  for feature in features:
    has_count = COUNT_RE.search(feature)
    if has_count:
      feature_counts.append((has_count.group(2), int(has_count.group(1))))
    else:
      feature_counts.append((feature, 1))
      
  return feature_counts
  
def group_by_hub(matches):
  hubs = {}
  for count, street, hub in matches:
    if hub in hubs:
      hubs[hub].append((count, street))
    else:
      hubs[hub] = [(count, street)]
  return hubs
  
###
  
def crawl():
  hubs = load_or_req('locations.getHubs')
  for hub_id in hubs['hubs']:
    print hub_id, hubs['hubs'][hub_id]['name']
    streets = load_or_req('locations.getStreets', {'hub_id': hub_id})
    for street_id in streets['streets']:
      print street_id, streets['streets'][street_id]['name']
      street_info = load_or_req('locations.streetInfo', {'street_tsid': street_id})
      print street_info

###

def stats(search_for):
  hubs = load_or_req('locations.getHubs')
  features = {}
  for hub_id in hubs['hubs']:
    streets = load_or_req('locations.getStreets', {'hub_id': hub_id})
    for street_id in streets['streets']:
      street_info = load_or_req('locations.streetInfo', {'street_tsid': street_id})
      street_features = extract_features(street_info)
      if not street_features:
        continue
      for feature, count in street_features:
        if feature in features:
          features[feature].append((count, street_info['name'], hubs['hubs'][hub_id]['name']))
        else:
          features[feature] = [(count, street_info['name'], hubs['hubs'][hub_id]['name'])]
  
  matches = []
  for feature in sorted(features.keys()):
    print feature, sum([c for c, _, _ in features[feature]])
    if feature.startswith(search_for):
      matches += features[feature]
      
  matches_by_hub = group_by_hub(matches)
  for hub in sorted(matches_by_hub):
    total = sum([count for count, _ in matches_by_hub[hub]])
    print hub, total
    for count, street in matches_by_hub[hub]:
      print '  ', count, street


#crawl()
if __name__ == '__main__':
  import sys
  import optparse
  parser = optparse.OptionParser()
  opts, args = parser.parse_args()
  
  stats(' '.join(args))
