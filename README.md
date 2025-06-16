This is a CLI application designed to take a file containing network flows recorded with [mitmproxy](https://mitmproxy.org/) capturing network traffic between a [Pixel Starships](https://pixelstarships.com/) (PSS) client and their servers and converting those flows into a schema description of the PSS API.

# How to use

## Standalone usage

- Install package
- Run `pssapiparser --help` for command help

# What does it do

The app parses the flows in the specified file and attempts to create a structure description of the PSS API based on that information. It tries to determine data types for query/request parameters and properties of objects returned by the PSS API. The output will be a list of dictionaries, one
per API service. Those dictionaries contain dictionaries, one per API endpoint. Each of those dictionaries contains information on a specific endpoint.

# Generate pssapi.py

```bash
# Generate code and put it into the folder ./bin 
pssapiparser gen ./bin ./examples/pss_api_complete_structure.json -e ./examples/pss_enums.json -c ./examples/pss_api_cacheable_endpoints.json
```
