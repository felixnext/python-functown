# This script is used to validate the function app deployment
# It serves as integration test
# WARNING: This script is untested

# default values
$FAPP = "functownexample"
$debug = $false

# parse parameters
$i = 0
while ($i -lt $args.Count) {
    switch ($args[$i]) {
        "--debug" {
            $debug = $true
            $i++
        }
        "--name" {
            $FAPP = $args[$i + 1]
            $i += 2
        }
        "--key" {
            $APP_KEY = $args[$i + 1]
            $i += 2
        }
        default {
            # unknown option
            $i++
        }
    }
}

# counter
$test_success = 0
$test_failed = 0

function red($message) {
    Write-Host -ForegroundColor Red $message
}

function green($message) {
    Write-Host -ForegroundColor Green $message
}

function blue($message) {
    Write-Host -ForegroundColor Blue $message
}

function bold($message) {
    Write-Host -ForegroundColor Black -BackgroundColor White $message
}

function make_request($body = "", $type = "GET", $query_param = "", $handler = "TestErrorHandler") {
    $response = Invoke-RestMethod -Method $type -Uri "https://$FAPP.azurewebsites.net/api/$handler?code=$APP_KEY" -Body $body -ContentType "application/json"
    return $response
}

function failed($reason, $response) {
    red "❌ Test failed ($reason)"
    red "Response: $response"
    $test_failed += 1
}

function validate_response {
    param (
        [string]$response = "",
        [string]$expected_completed = "false",
        [string]$expected_keys = "",
        [string]$expected_key_values = ""
    )
    $keys = $expected_keys -split "|"
    $dict = $expected_key_values -split "|"

    # parse data
    $completed = $response | ConvertFrom-Json | Select-Object -ExpandProperty completed
    $req_param = $response | ConvertFrom-Json | Select-Object -ExpandProperty results.req_param

    # check completed
    if (($completed -ne $expected_completed) -and (($completed -ne $null) -or ($expected_completed -ne "false"))) {
        Write-Host "Failed: completed: $completed - expected: $expected_completed"
        return
    }

    # iterate all splitted keys and check if in response
    foreach ($key in $keys) {
        $value = $response | ConvertFrom-Json | Select-Object -ExpandProperty $key

        if ([string]::IsNullOrEmpty($value) -or ($value -eq $null)) {
            Write-Host "Failed: key $key not found"
            return
        }
    }

    # check if all key-value pairs are in response
    foreach ($pair in $dict) {
        $key, $value = $pair -split ":"
        $response_value = $response | ConvertFrom-Json | Select-Object -ExpandProperty $key

        if ($response_value -ne $value) {
            Write-Host "Failed: key $key not equal to $value - $response_value"
            return
        }
    }

    # test was successful
    Write-Host "✅ Test passed"
    $test_success += 1
}

function run_test_case {
    param ($name = "", $body = "", $type = "GET", $query_param = "", $handler = "TestErrorHandler", $completed = "true", $expected_keys = "", $expected_key_values = "")

    Write-Host ""
    Write-Host "--- TEST [$handler::$type]: $name ---" -ForegroundColor Blue -BackgroundColor White

    $response = make_request $body $type $query_param $handler

    # validate if response is correct
    if ($response -eq $null) {
        failed "response empty" $response
    }
    else {
        validate_response $response $completed $expected_keys $expected_key_values
    }
}

function echo_header {
    param ($name = "")
    Write-Host ""
    Write-Host "======================================"
    Write-Host "Testing $name" -ForegroundColor Blue -BackgroundColor White
    Write-Host "======================================"
}

Write-Host "Validating $FAPP"

# --- ErrorHandler ---
echo_header "ErrorHandler"
$hdl = "TestErrorHandler"

# Minimal tests
run_test_case "Minimal" '{"req": "1", "body_param": "foo"}' "POST" "" $hdl "true" "logs|results.body_param" "results.use_exeption:false|results.body_param:foo"
run_test_case "Minimal" "" "GET" "req=1&query_param=foo" $hdl "true" "logs|results.body_param" "results.use_exeption:false|results.query_param:foo"

# Required Missing
run_test_case "Required Missing" '{}' "POST" "" $hdl "false" "trace|user_message|logs" "type:<class 'functown.errors.errors.ArgError'>"
run_test_case "Required Missing" "" "GET" "use_event=false&use_logger=false" $hdl "false" "trace|user_message|logs" "type:<class 'functown.errors.errors.ArgError'>"

# Exception
run_test_case "Exception" '{"req": 1, "use_exception": true}' "POST" "" $hdl "false" "trace|user_message|logs" "type:<class 'Exception'>"

# printing
run_test_case "Printing" '{"req": 1, "print_list": [1,2,3]}' "POST" "" $hdl "true" "logs|results.body_param" "results.print_list:[ 1, 2, 3 ]"

# --- Events ---
echo_header "Insights Events"
$hdl = "TestInsightsEvents"

run_test_case "Event" '{"use_event": true}' "POST" "" $hdl "true" "logs|results.use_event" "results.use_event:true"

# --- Logs ---
echo_header "Insights Logger"
$hdl = "TestInsightsLogs"

run_test_case -name "Logger" -body '{"use_logger": true}' -type "POST" -query_param "" -handler $hdl -completed "true" -expected_keys "logs|results.use_logger" -expected_key_values "results.use_logger:true|results.use_tracer:false"

run_test_case -name "Tracer" -body '{"use_tracer": true}' -type "POST" -query_param "" -handler $hdl -completed "true" -expected_keys "logs|results.use_tracer" -expected_key_values "results.use_tracer:true|results.use_logger:false"

# --- Metrics ---
echo_header "Insights Metrics"
$hdl = "TestInsightsMetrics"

run_test_case -name "Metric" -body '{"counter": 10, "gauge": 5, "sum": 4}' -type "POST" -query_param "" -handler $hdl -completed "true" -expected_keys "logs|results.sleep_sec" -expected_key_values "results.counter.data:10|results.gauge.data:5|results.sum.data:4"
