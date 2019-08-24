# Microsoft Domain/IP Listing Tool
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/74ff3a4bfce34a1d9f867634eaafaf6b)](https://app.codacy.com/app/NathanVaughn/MDIPLT?utm_source=github.com&utm_medium=referral&utm_content=NathanVaughn/MDIPLT&utm_campaign=Badge_Grade_Dashboard)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/e155e666288249a88c01eed0ed8fa261)](https://www.codacy.com/app/NathanVaughn/MDIPLT?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=NathanVaughn/MDIPLT&amp;utm_campaign=Badge_Grade)

A small Python program to parse [Microsoft's list of URLs and IP](https://docs.microsoft.com/en-us/Office365/Enterprise/office-365-ip-web-service) and generate simple output files.

## Requirements

Just Python 3. Everything is written with the standard library.

## Usage

```text
usage: microsoft_domains.py [-h] [--required] [--ignorecache]
                            [--outfile OUTFILE] [--append]
                            {worldwide,usgovdod,usgovgcchigh,china,germany}
                            {urls,ips}

Microsoft Domain/IP Listing Tool

positional arguments:
  {worldwide,usgovdod,usgovgcchigh,china,germany}
                        Region to select from
  {urls,ips}            Item to get data for

optional arguments:
  -h, --help            show this help message and exit
  --required            Only collect items that are marked as required.
                        Otherwise, collect all items
  --ignorecache         Forces a cache refresh
  --outfile OUTFILE     Output to given file
  --append              Append to output file instead of the default of
                        writing a new file
```

### Outputs

#### File

If you provide the `--outfile=filename` argument, a file in the
current working directory will be generated with a list of the requested items,
with one item per line. This will overwrite any existing file.

Example:
```bash
python microsoft_domains.py worldwide urls --outfile=world_urls.txt
```

Including the `--append` argument will do the same thing, except append the text
if a file of the same name already exists instead of overwriting it.

#### Console

If you do not provide an output file, the output will instead be printed to the
console `stdout`. Messages to the user are printed to `stderror`.

### Caching

While not rate-limited, to help you comply with Microsoft's suggestion to
"check the version not more than once an hour", a caching system is implemented
to cache results for an hour at a time.
This can be bypassed with the `--ignorecache` argument.

However, this will not bypass the cache for getting
the list of regions, as this changes extremely rarely, and this is
needed by the script in order to process the region argument.
If you absolutely need, you can delete the `msdomaincache/regions.cache` file.