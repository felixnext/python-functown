#!/bin/bash
# This script is used to validate the function app deployment
# It serves as integration test

FAPP="functownexample"

function red(){
    echo -e "\x1B[31m $1 \x1B[0m"
}

function green(){
    echo -e "\x1B[32m $1 \x1B[0m"
}

function blue(){
    echo -e "\x1B[34m $1 \x1B[0m"
}

function bold(){
    echo -e "\x1B[1m $1 \x1B[0m"
}

while [[ $# -gt 0 ]]
    do
    key="$1"

    case --key in
        $key)
        key="$2"
        shift # past argument
        ;;
        *)
                # unknown option
        ;;
    esac
        shift # past value
done

echo "Validating function app: $FAPP"
# echo "Key: $key"

function make_request() {
    local body=${1:-""}
    local type=${2:-"GET"}
    local query_param=${3:-""}
    local handler=${4:-"TestErrorHandler"}
    local response

    if [[ "$type" == "POST" ]]; then
        response=$(curl -X POST -H "Content-Type: application/json" -d "$body" "https://${FAPP}.azurewebsites.net/api/$handler?code=${key}")
    else
        response=$(curl -X GET "https://${FAPP}.azurewebsites.net/api/$handler?code=${key}&$query_param")
    fi

    echo $response
}

function validate_response() {
    # response
    local response=${1:-""}
    # bool to check if complete
    local expected_completed=${2:-"false"}
    # expected key items (e.g. "logs,trace")
    local expected_keys=${3:-""}
    # expected key-value pairs (e.g. "type:<class 'functown.errors.errors.ArgError'>")
    local expected_key_values=${4:-""}
    local keys=()
    local dict=()

    # parse expected_keys into array and store in keys
    IFS=',' read -ra keys <<< "$expected_keys"
    IFS=',' read -ra dict <<< "$expected_key_values"

    # parse data
    local completed=$(echo $response | jq '.completed')
    local req_param=$(echo $response | jq '.results.req_param')

    # check completed
    if [ "$completed" != "$expected_completed" ]; then
        red "Test failed (completed not equal)"
        exit 1
    fi

    # iterate all splitted keys and check if in response
    for key in "${keys[@]}"; do
        local value=$(echo $response | jq ".$key")

        if [ -z "$value" ] || [ "$value" == "null" ]; then
            red "Test failed (key $key not found)"
            red "Response: $response"
            exit 1
        fi
    done

    # check if all key-value pairs are in response
    for pair in "${dict[@]}"; do
        local key=$(echo $pair | cut -d':' -f1)
        local value=$(echo $pair | cut -d':' -f2)
        local response_value=$(echo $response | jq ".$key")

        if [ "$response_value" != "$value" ]; then
            red "Test failed (key $key not equal to $value - $response_value)"
            red "Response: $response"
            exit 1
        fi
    done

    green "Test passed"
}

function run_test_case() {
    local name=${1:-""}
    local body=${2:-""}
    local type=${3:-"GET"}
    local query_param=${4:-""}
    local handler=${5:-"TestErrorHandler"}
    local completed=${6:-"true"}
    local expected_keys=${7:-""}
    local expected_key_values=${8:-""}

    bold "$(blue "--- TEST [$handler::$type]: $name ---")"
    response=$(make_request "$body" "$type" "$query_param" "$handler")

    # validate if response is correct
    if [ -z "$response" ]; then
        red "Test failed (response empty)"
        red "Response: $response"
    else
        validate_response "$response" "$completed" "$expected_keys" "$expected_key_values"
    fi
}

function echo_header() {
    local name="${1:-""}"
    echo "======================================"
    bold "$(blue "Testing $name")"
    echo "======================================"
}

# --- ErrorHandler ---
echo_header "ErrorHandler"

# Test 1
run_test_case "Minimal" '{"req": "1", "use_event": true, "use_logger": true}' "POST" "" "TestErrorHandler" "true" "logs,results.body_param" "results.use_exeption:false"

# Test 2
run_test_case "Minimal" "" "GET" "req=2&use_event=false&use_logger=false" "TestErrorHandler" "false", "trace", ""

# TODO: add more test cases

