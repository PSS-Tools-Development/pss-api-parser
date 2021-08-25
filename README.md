This is a tool designed to take a file containing network flows recorded with [mitmproxy](https://mitmproxy.org/) capturing network traffic between a [Pixel Starships](https://pixelstarships.com/) (PSS) client and their servers and converting those flows into a schema description of the PSS API.

# How to use

- Run `parse.py` - this module expects one command line parameter: the path to the file containing the recorded flows.
- The module will do its work and create (or overwrite) a JSON file with the same name in the same directory as specified (with file extension `.json`)

# What does it do

The module parses the flows in the specified file and attempts to create a structure description of the PSS API based on that information. It tries to determine data types for query/request parameters and properties of objects returned by the PSS API.