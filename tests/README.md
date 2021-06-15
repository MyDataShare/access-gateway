
# TODO

## Route arguments

Test that route arguments can be used within the gateway. NOTE: Test all http methods.

### Can be passed to response

Test that input data (headers, query params, etc.) can be passed to response.

* headers
    * One header
    * Two headers
    * With dash
    * All headers (copy)
* dynamic (parts of url)
* query params
    * One
    * Two
    * Array
    * All (copy)
* text payload
* json payload
    * One value
    * Two values
    * Array
    * Dict
    * Copy
* data payload
    * One value
    * Two values
    * Array
    * Copy

### Can be passed to requests

Test that input data (headers, query params, etc.) can be passed to requests.

Same test set as above but pass data to requests and create mock_dp routes that expect the data and return test name
back. Use the mock_dp returned test name in the response returned by AGW.

## Request response

Test that request responses can be used within gateway.

### Can be passed to next request


### Can be passed to response




