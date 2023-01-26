#!/bin/bash
# This script is used to validate the function app deployment
# It serves as integration test

FAPP="functownexample"

# parse the arguments (key)
while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
        -k|--key)
            key="$2"
            shift
            ;;
        *)
            # unknown option
            ;;
    esac
    shift
done

make_request() {
    local body=${body:-""}
    local type=${type:-"GET"}
    local query_param=${query_param:-""}
    local handler=${handler:-"TestErrorHandler"}
    local response
    if [[ "$type" == "POST" ]]; then
        response=$(curl -X POST -H "Content-Type: application/json" -d "$body" "https://${FAPP}.azurewebsites.net/api/$handler?code=${key}")
    else
        response=$(curl -X GET "https://${FAPP}.azurewebsites.net/api/$handler?code=${key}&$query_param")
    fi
    echo "$response"
}

validate_response() {
    local response=${response:-""}
    local expected_completed=${expected_completed:-"false"}
    local expected_req_param=${expected_req_param:-"0"}
    local completed=$(echo $response | jq '.completed')
    local req_param=$(echo $response | jq '.results.req_param')
    if [ "$completed" != "$expected_completed" ] || [ "$req_param" != "$expected_req_param" ]; then
        echo "Test failed"
    else
        echo "Test passed"
    fi
}

# Test 1
# TODO: out into a function
echo "--- Test 1 ---"
response=$(make_request body='{"req": "1", "use_event": true, "use_logger": true}' type="POST" query_param="" handler="TestErrorHandler")
# check if response is empty
if [ -z "$response" ]; then
    echo "Test failed (response empty)"
else
    validate_response response="$response" expected_completed="true" expected_req_param="1"
fi

# Test 2
response=$(make_request type="GET" query_param='req=2&use_event=false&use_logger=false' handler="TestErrorHandler")
validate_response response="$response" expected_completed="true" expected_req_param="2"

# Add more test cases as needed

