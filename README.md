This is a tool designed to take a file containing network flows recorded with [mitmproxy](https://mitmproxy.org/) capturing network traffic between a [Pixel Starships](https://pixelstarships.com/) (PSS) client and their servers and converting those flows into a schema description of the PSS API.

# How to use

## Standalone usage

- Run `parse.py` - this module expects one command line parameter: the path to the file containing the recorded flows.
- The module will do its work and create (or overwrite) a JSON file with the same name in the same directory as the file specified (but with file extension `.json`)


## As imported module

- Import the module `parse`
- Execute the function `parse_flows_file`. The function returns a nested dictionary resembling the structure of the API.


# What does it do

The module parses the flows in the specified file and attempts to create a structure description of the PSS API based on that information. It tries to determine data types for query/request parameters and properties of objects returned by the PSS API. The output will be a list of dictionaries, one per API service. Those dictionaries contain dictionaries, one per API endpoint. Each of those dictionaries contains information on a specific endpoint.