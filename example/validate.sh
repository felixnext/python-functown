#!/bin/bash
# This script is used to validate the function app deployment
# It serves as integration test

# execute:
# ./validate.sh --name <function app name> --key <function app key>

# default values
FAPP="functownexample"
debug=false

# parse parameters
while [[ $# -gt 0 ]]
    do
    case $1 in
        --debug)
        debug=true
        shift # past argument
        ;;
        --name)
        FAPP="$2"
        shift # past argument
        shift # past value
        ;;
        --key)
        APP_KEY="$2"
        shift # past argument
        shift # past value
        ;;
        *)
                # unknown option
        ;;
    esac
done

# counter
test_success=0
test_failed=0


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

function make_request() {
    local body=${1:-""}
    local type=${2:-"GET"}
    local query_param=${3:-""}
    local handler=${4:-"TestErrorHandler"}
    local response

    if [[ "$type" == "POST" ]]; then
        response=$(curl -s -X POST -H "Content-Type: application/json" -d "$body" "https://${FAPP}.azurewebsites.net/api/$handler?code=${APP_KEY}")
    else
        response=$(curl -s -X GET "https://${FAPP}.azurewebsites.net/api/$handler?code=${APP_KEY}&$query_param")
    fi

    echo $response
}

function failed() {
    local reason=${1:-""}
    local response=${2:-""}
    red "❌ Test failed ($reason)"
    red "Response: $response"
    test_failed=$((test_failed+1))
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
    IFS='|' read -ra keys <<< "$expected_keys"
    IFS='|' read -ra dict <<< "$expected_key_values"

    # parse data
    local completed=$(echo $response | jq '.completed')
    local req_param=$(echo $response | jq '.results.req_param')

    # check completed
    if [[ ("$completed" != "$expected_completed") && (("$completed" != "null") || ("$expected_completed" != "false")) ]]; then
        failed "completed: $completed - expected: $expected_completed" "$response"
        return
    fi

    # iterate all splitted keys and check if in response
    for key in "${keys[@]}"; do
        local value=$(echo $response | jq ".$key")

        if [ -z "$value" ] || [ "$value" == "null" ]; then
            failed "key $key not found" "$response"
            return
        fi
    done

    # check if all key-value pairs are in response
    for pair in "${dict[@]}"; do
        local key=$(echo $pair | cut -d':' -f1)
        local value=$(echo $pair | cut -d':' -f2)
        local response_value=$(echo $response | jq ".$key")

        # remove double quotes and single quotes around value
        value=$(echo $value | sed -e 's/^"//' -e 's/"$//')
        value=$(echo $value | sed -e "s/^'//" -e "s/'$//")
        response_value=$(echo $response_value | sed -e 's/^"//' -e 's/"$//')
        response_value=$(echo $response_value | sed -e "s/^'//" -e "s/'$//")

        if [ "$response_value" != "$value" ]; then
            failed "key $key not equal to $value - $response_value" "$response"
            return
        fi
    done

    # test was successful
    green "✅ Test passed"
    if [ "$debug" = true ]; then
        green "Response: $response"
    fi
    test_success=$((test_success+1))
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
        failed "response empty" "$response"
    else
        validate_response "$response" "$completed" "$expected_keys" "$expected_key_values"
    fi
}

function echo_header() {
    local name="${1:-""}"
    echo ""
    echo "======================================"
    bold "$(blue "Testing $name")"
    echo "======================================"
}

echo "Validating $FAPP"

# --- ErrorHandler ---
echo_header "ErrorHandler"
hdl="TestErrorHandler"

# Minimal tests
run_test_case "Minimal" '{"req": "1", "body_param": "foo"}' "POST" "" "$hdl" "true" "logs|results.body_param" "results.use_exeption:false|results.body_param:foo"
run_test_case "Minimal" "" "GET" "req=1&query_param=foo" "$hdl" "true" "logs|results.body_param" "results.use_exeption:false|results.query_param:foo"

# Required Missing
run_test_case "Required Missing" '{}' "POST" "" "$hdl" "false" "trace|user_message|logs" "type:<class 'functown.errors.errors.ArgError'>"
run_test_case "Required Missing" "" "GET" "use_event=false&use_logger=false" "$hdl" "false" "trace|user_message|logs" "type:<class 'functown.errors.errors.ArgError'>"

# Exception
run_test_case "Exception" '{"req": 1, "use_exception": true}' "POST" "" "$hdl" "false" "trace|user_message|logs" "type:<class 'Exception'>"

# printing
run_test_case "Printing" '{"req": 1, "print_list": [1,2,3]}' "POST" "" "$hdl" "true" "logs|results.body_param" "results.print_list:[ 1, 2, 3 ]"

# --- Events ---
echo_header "Insights Events"
hdl="TestInsightsEvents"

run_test_case "Event" '{"use_event": true}' "POST" "" "$hdl" "true" "logs|results.use_event" "results.use_event:true"

# --- Logs ---
echo_header "Insights Logger"
hdl="TestInsightsLogs"

run_test_case "Logger" '{"use_logger": true}' "POST" "" "$hdl" "true" "logs|results.use_logger" "results.use_logger:true|results.use_tracer:false"

run_test_case "Tracer" '{"use_tracer": true}' "POST" "" "$hdl" "true" "logs|results.use_tracer" "results.use_tracer:true|results.use_logger:false"

# --- Metrics ---
echo_header "Insights Metrics"
hdl="TestInsightsMetrics"

run_test_case "Metric" '{"counter": 10, "gauge": 5, "sum": 4}' "POST" "" "$hdl" "true" "logs|results.sleep_sec" "results.counter.hits:10|results.counter.data:[ 10 ]|results.gauge.data:[ 10 ]|results.sum.data:[ 6.5 ]"

# --- Json Serialization ---
echo_header "Json Serialization"
hdl="TestJsonSerialization"

run_test_case "Json" '{"foo": "bar"}' "POST" "" "$hdl" "true" "" "foo:bar|processed:true"

# --- Protobuf Serialization ---
echo_header "Protobuf Serialization"
hdl="TestProtobufSerialization"

msg='\nM\n\x0bHello World\x10\x01\x1d\x00\x00\x00?"\x11\n\rHello World 0\x10\x00"\x11\n\rHello World 1\x10\x00"\x11\n\rHello World 2\x10\x00'

# FEAT: find a way to check deserialization
# run_test_case "Protobuf" "$msg" "POST" "" "$hdl" "true" "" "foo:bar|processed:true"

# --- Statistics ---
# print pretty statistics about failed and successful tests
echo ""
echo "======================================"
bold "$(blue "Test Results")"
echo "======================================"
green "Success: $test_success"
red "Failed: $test_failed"
percentage=$(echo "scale=2; $test_success / ($test_success + $test_failed) * 100" | bc)
if [ $(echo "$percentage < 100" | bc) -eq 1 ]; then
    red "Percentage: $percentage%"
else
    green "Percentage: $percentage%"
fi

echo "======================================"
