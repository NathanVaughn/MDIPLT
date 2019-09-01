"""
Microsoft Domain/IP Listing Tool
"""

from __future__ import print_function

import argparse
import json
import os
import sys
import time
import urllib.request
import uuid
from collections import OrderedDict

# base path that the api is served from
BASE_PATH = "https://endpoints.office.com"
# absolute directory this file resides in, plus cache folder
CACHE_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "msdomaincache"))
# one hour in seconds
CACHE_TIMEOUT = 3600


def eprint(*args, **kwargs):
    """Print values to stderror"""

    print(*args, file=sys.stderr, **kwargs)


# =============
# URL
# =============


def build_url(url):
    """Generates full request url with UUID and requested format"""

    # generate uuid
    uid = str(uuid.uuid4())
    # specify format. JSON is the default, but doesn't hurt to be explicit
    # "format" is a builtin function, so chose something different to avoid confusion
    frmt = "json"

    # url encode the data
    data = {"clientrequestid": uid, "format": frmt}
    url_values = urllib.parse.urlencode(data)

    # generate and return new url
    return url + "?" + url_values


def make_request(url):
    """Makes HTTP GET request to the given URL"""

    # open the url
    eprint("Making request to {}".format(url))
    data = urllib.request.urlopen(url) #nosec

    # return the decoded result
    return data.read().decode()


# =============
# JSON
# =============


def parse_json(string):
    """Parses JSON string and returns dictionary"""

    return json.loads(string)


def get_json_from_url(url):
    """Returns dictionary from a URL which returns JSON"""

    full_url = build_url(url)
    result = make_request(full_url)
    return parse_json(result)


# =============
# Caching
# =============


def cache_avail(cache_file):
    """Checks if the given cache file exists and has not expired"""

    try:
        # check if current time minus last modified time is less than the cache timeout
        return bool(time.time() - os.path.getmtime(cache_file) < CACHE_TIMEOUT)
    except OSError:
        # if file does not exist or is inaccessible
        return False


def load_cache(cache_file):
    """Loads the given JSON cache file and returns the data"""

    # open cache file
    with open(cache_file, "r") as cache_f:
        # read data in
        data = cache_f.read()

    # parse as json
    return parse_json(data)


def write_cache(cache_file, data):
    """Creates a cache file with the given data"""

    # if cache folder does not exist, create it
    if not os.path.exists(CACHE_FOLDER):
        os.mkdir(CACHE_FOLDER)

    # open cache file, and write data to it as json
    with open(cache_file, "w") as cache_f:
        cache_f.write(json.dumps(data))


def use_cache(cache_file_name, operation, ignorecache=False):
    """
    Wrapper function to use cache

    Uses given cache file and operation to perform, and tries to load the cache. If that
    fails, it will run the operation and create the cache.

    Parameters:
    cache_file_name (str): Relative filename to use for the cache file.
        Path will be built from this.
    operation (fun): Function handle to execute and use return value of.
    ignorecache (bool): Boolean to ignore cache and forecefully regnerate it.

    Returns:
    data: Return data from cache file or operation, whicever was used
    """

    def build_cache(cache_file, operation):
        data = operation()
        write_cache(cache_file, data)
        return data

    cache_file = os.path.join(CACHE_FOLDER, cache_file_name)

    # test if cache is available, and not ignored
    if cache_avail(cache_file) and not ignorecache:
        try:
            # if so, try to load it
            data = load_cache(cache_file)
            eprint("Using cache {}".format(os.path.basename(cache_file)))
        except json.decoder.JSONDecodeError:
            eprint("Cache corrupted")
            # if cache is corrupted, rebuild
            data = build_cache(cache_file, operation)
    else:
        eprint("Ignoring cache")
        # rebuild
        data = build_cache(cache_file, operation)

    return data


# =============
# Data
# =============


def get_regions_data():
    """Get data for the current region names and versions"""

    # operation function
    def get_regions_data_operation():
        base_url = BASE_PATH + "/version"
        regions = get_json_from_url(base_url)
        return regions

    # use cache
    cache_file = "regions.cache"
    return use_cache(cache_file, get_regions_data_operation)


def get_regions_list():
    """Convert regions data into a list of region names"""

    regions_data = get_regions_data()
    # convert regions data to a simple list
    return [region["instance"] for region in regions_data]


def get_endpoint_data(region, ignorecache):
    """Get endpoint data for the given region"""

    # operation function
    def get_endpoint_data_operation(region):
        base_url = BASE_PATH + "/endpoints/{}".format(region)
        data = get_json_from_url(base_url)
        return data

    # use cache
    cache_file = "{}.cache".format(region)
    return use_cache(
        cache_file, lambda: get_endpoint_data_operation(region), ignorecache
    )


def get_items(region, item, required, ignorecache):
    """
    Gets the desired item from the given region with the given filters

    Parameters:
    region (str): Region to pull data from
    item (str): Item to collect (IPs or URLs)
    required (bool): If True, only collect items from services in the region that are
        marked as 'required'
    ignorecache (bool): Boolean to ignore cache and forecefully regnerate it.

    Returns:
    data: Returns a sorted, unique list of the collected items
    """

    data = get_endpoint_data(region, ignorecache)

    items = []

    for service in data:
        # for each service in the data
        if item in service:
            # if the service contains the requested resources (ips, urls)
            if not (not service["required"] and required):
                # if the service is not considered required and the user
                # only wants required items, don't add it to the list. Otherwise, add it
                items.extend(service[item])

    # easy way to remove duplicates from a list while keeping the items in order
    items.sort()
    return list(OrderedDict.fromkeys(items))


def write_to_file(filename, data, append=False):
    """Writes data to given file"""
    if append:
        # append file
        mode = "a"
    else:
        # write new file
        mode = "w"

    with open(filename, mode) as out_f:
        # get length of data
        leng = len(data)
        # iterate through data
        for i, line in enumerate(data):
            # write data
            out_f.write(line)
            # write new line unless it is last item
            if i < leng - 1:
                out_f.write("\n")

    eprint("Wrote to {}".format(filename))


def main():
    """Main function"""

    parser = argparse.ArgumentParser(description="Microsoft Domain/IP Listing Tool")

    regions = get_regions_list()
    regions = [region.lower() for region in regions]

    items = ["urls", "ips"]

    parser.add_argument(
        "region", type=str.lower, choices=regions, help="Region to select from"
    )
    parser.add_argument(
        "item", type=str.lower, choices=items, help="Item to get data for"
    )
    parser.add_argument(
        "--required",
        action="store_true",
        help="Only collect items that are marked as required. Otherwise,"
        " collect all items",
    )
    parser.add_argument(
        "--ignorecache", action="store_true", help="Forces a cache refresh"
    )
    parser.add_argument("--outfile", type=str, help="Output to given file")
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to output file instead of the default of writing a new file",
    )

    args = parser.parse_args()

    data = get_items(args.region, args.item, args.required, args.ignorecache)
    if args.outfile:
        write_to_file(args.outfile, data, args.append)
    else:
        for line in data:
            print(line)


if __name__ == "__main__":
    main()
