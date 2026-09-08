$ErrorActionPreference = 'Stop'
$logFile = 'c:/Users/MadhaviRambha/STLC-CapstoneProject/artifacts/Requirements/jira_creation_result.log'
if (Test-Path $logFile) { Remove-Item $logFile -Force }

function Log([string]$line) {
    Add-Content -Path $logFile -Value $line
}

Log 'START'
Write-Output 'STEP:START'

try {

$envFile = 'c:/Users/MadhaviRambha/STLC-CapstoneProject/env/api-jira.env'
Get-Content $envFile | ForEach-Object {
    if (-not ($_ -match '^\s*#' -or $_ -match '^\s*$')) {
        $parts = $_ -split '=', 2
        if ($parts.Count -eq 2) {
            $k = $parts[0].Trim()
            $v = $parts[1].Trim()
            if ($k -ne 'JIRA_PROJECT_KEY') {
                [Environment]::SetEnvironmentVariable($k, $v, 'Process')
            }
        }
    }
}

$projectKey = 'SC'
$base = $env:JIRA_BASE_URL.TrimEnd('/')
Log 'STEP:ENV_LOADED'
Write-Output 'STEP:ENV_LOADED'
$pair = ('{0}:{1}' -f $env:JIRA_EMAIL, $env:JIRA_API_TOKEN)
$basic = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
$headers = @{
    Authorization = ('Basic {0}' -f $basic)
    Accept = 'application/json'
    'Content-Type' = 'application/json'
}

function New-Adf([string]$text) {
    $lines = $text -split "`n"
    $content = @()
    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            $content += @{ type = 'paragraph'; content = @() }
        } else {
            $content += @{ type = 'paragraph'; content = @(@{ type = 'text'; text = $line }) }
        }
    }

    return @{ type = 'doc'; version = 1; content = $content }
}

function Create-Issue($summary, $issueTypeId, $descriptionText, $parentKey = $null) {
    $fields = @{
        project = @{ key = $projectKey }
        summary = $summary
        issuetype = @{ id = $issueTypeId }
        description = (New-Adf $descriptionText)
    }

    if ($parentKey) {
        $fields.parent = @{ key = $parentKey }
    }

    $payload = @{ fields = $fields } | ConvertTo-Json -Depth 20
    $resp = Invoke-RestMethod -Uri "$base/rest/api/3/issue" -Headers $headers -Method Post -Body $payload
    return $resp.key
}

$workstreamTypeId = '10183'
$taskTypeId = '10184'
$subtaskTypeId = '10185'
Log 'STEP:TYPES_READY'
Write-Output 'STEP:TYPES_READY'

$epicKey = Create-Issue -summary 'Epic: SauceDemo E-commerce Shopping Experience' -issueTypeId $workstreamTypeId -descriptionText @"
Covers end-to-end SauceDemo capabilities from authentication to order completion.
Includes login, product discovery, cart management, checkout, logout, and usability expectations.
"@
Log ('STEP:EPIC_CREATED ' + $epicKey)
Write-Output ('STEP:EPIC_CREATED ' + $epicKey)

$features = @(
    @{ Summary = 'Feature: Authentication and Session Management'; Desc = 'Includes login validation, invalid credential handling, protected route access, and secure logout.' },
    @{ Summary = 'Feature: Product Catalog and Sorting'; Desc = 'Includes product listing with details and sorting by name and price.' },
    @{ Summary = 'Feature: Shopping Cart Management'; Desc = 'Includes add to cart, view cart details, item removal, and cart state updates.' },
    @{ Summary = 'Feature: Checkout and Order Completion'; Desc = 'Includes checkout initiation, customer info capture, order summary, and successful order placement.' },
    @{ Summary = 'Feature: Responsive UX and Performance'; Desc = 'Includes mobile/desktop responsiveness, clear error feedback, and expected page/data load performance.' }
)

$featureKeys = @{}
foreach ($f in $features) {
    $featureKeys[$f.Summary] = Create-Issue -summary $f.Summary -issueTypeId $taskTypeId -descriptionText $f.Desc -parentKey $epicKey
}

$stories = @(
    @{ Summary = 'US-001: Login with valid credentials'; Feature = 'Feature: Authentication and Session Management'; Body = "As a registered shopper,`nI want to log in with a valid username and password,`nSo that I can access products and purchase items.`n`nAcceptance Criteria:`n- Given I am on the login page, when I enter valid credentials and submit, then I am redirected to the products page.`n- Given I submit invalid credentials, then an error message is displayed and I remain on the login page.`n- Given I leave username or password empty, then a clear validation or error message is shown.`n- Given I am logged in, when I refresh a protected page, then my authenticated session remains valid until logout or timeout." },
    @{ Summary = 'US-002: View product catalog'; Feature = 'Feature: Product Catalog and Sorting'; Body = "As a logged-in shopper,`nI want to view all available products with details,`nSo that I can decide what to buy.`n`nAcceptance Criteria:`n- Given I am logged in, when products page loads, then each product shows name, image, description, and price.`n- Given product data is available, then catalog content is loaded within 2 seconds under normal conditions.`n- Given I am not logged in, when I try to access products page directly, then I am redirected to login.`n- Given an application or data issue occurs, then a clear error message is shown to the user." },
    @{ Summary = 'US-003: Sort products'; Feature = 'Feature: Product Catalog and Sorting'; Body = "As a logged-in shopper,`nI want to sort products by name and price,`nSo that I can find items faster.`n`nAcceptance Criteria:`n- Given I am on products page, when I choose Name (A to Z), then products are sorted alphabetically ascending.`n- Given I choose Name (Z to A), then products are sorted alphabetically descending.`n- Given I choose Price (Low to High), then products are sorted by ascending numeric price.`n- Given I choose Price (High to Low), then products are sorted by descending numeric price.`n- Given sorting is applied, then visible product details remain accurate for each item." },
    @{ Summary = 'US-004: Add item to cart'; Feature = 'Feature: Shopping Cart Management'; Body = "As a logged-in shopper,`nI want to add products to my cart,`nSo that I can purchase selected items later.`n`nAcceptance Criteria:`n- Given I am logged in, when I click Add to cart on a product, then that product is added to cart.`n- Given an item is added, then cart badge or count updates immediately.`n- Given I am not logged in, when I attempt add-to-cart behavior, then access is blocked and I am sent to login.`n- Given multiple items are added, then each selected item appears in cart with correct price and quantity." },
    @{ Summary = 'US-005: View and manage cart'; Feature = 'Feature: Shopping Cart Management'; Body = "As a logged-in shopper,`nI want to view cart contents and remove items,`nSo that I can control what I buy.`n`nAcceptance Criteria:`n- Given I open the cart, then all selected items are listed with names, quantities, and prices.`n- Given an item is in cart, when I remove it, then it no longer appears in cart.`n- Given item removal occurs, then cart badge or count updates accurately.`n- Given no items remain, then cart displays an empty state and checkout is disabled or blocked." },
    @{ Summary = 'US-006: Start checkout'; Feature = 'Feature: Checkout and Order Completion'; Body = "As a logged-in shopper,`nI want to proceed to checkout from cart,`nSo that I can complete my purchase.`n`nAcceptance Criteria:`n- Given cart has at least one item, when I click Checkout, then I navigate to checkout information step.`n- Given cart is empty, when I click Checkout, then I am blocked with a clear message.`n- Given I am not authenticated, when I try to reach checkout, then I am redirected to login." },
    @{ Summary = 'US-007: Enter checkout information'; Feature = 'Feature: Checkout and Order Completion'; Body = "As a shopper in checkout,`nI want to provide first name, last name, and postal code,`nSo that my order can be processed.`n`nAcceptance Criteria:`n- Given I am on checkout information page, then fields for first name, last name, and postal code are present.`n- Given any required field is missing, when I continue, then checkout does not proceed and a clear error message appears.`n- Given all required fields are valid, when I continue, then I move to order overview step.`n- Given invalid format or empty values are entered, then user-friendly validation feedback is displayed." },
    @{ Summary = 'US-008: Review order summary and complete purchase'; Feature = 'Feature: Checkout and Order Completion'; Body = "As a shopper in checkout,`nI want to review order summary and finalize purchase,`nSo that I can place my order confidently.`n`nAcceptance Criteria:`n- Given I reach overview step, then I see selected items, pricing, and totals before finishing.`n- Given I click Finish with valid checkout state, then order is completed and confirmation or success message is shown.`n- Given order completes, then cart is cleared.`n- Given checkout prerequisites are not met, then finish action is blocked with clear feedback." },
    @{ Summary = 'US-009: Logout securely'; Feature = 'Feature: Authentication and Session Management'; Body = "As an authenticated user,`nI want to log out from any page,`nSo that my session is securely ended.`n`nAcceptance Criteria:`n- Given I am logged in on any page, when I click Logout, then I am redirected to login page.`n- Given I have logged out, when I use browser back to protected pages, then access is denied and redirected to login.`n- Given logout occurs, then session or auth state is invalidated." },
    @{ Summary = 'US-010: Responsive and usable experience'; Feature = 'Feature: Responsive UX and Performance'; Body = "As a shopper,`nI want the application to work well on desktop and mobile,`nSo that I can shop from any device.`n`nAcceptance Criteria:`n- Given supported desktop or mobile viewport, then pages render without broken layouts or overlap.`n- Given core flows (login, catalog, cart, checkout, logout), then each flow is usable on both desktop and mobile.`n- Given invalid user actions, then clear error messages are shown.`n- Given product and cart views load, then data appears within 2 seconds under expected environment conditions." }
)

$createdStories = @()
foreach ($s in $stories) {
    $parentFeatureKey = $featureKeys[$s.Feature]
    $storyKey = Create-Issue -summary $s.Summary -issueTypeId $subtaskTypeId -descriptionText $s.Body -parentKey $parentFeatureKey
    $createdStories += ("{0} -> parent {1}" -f $storyKey, $parentFeatureKey)
}

Log ("Created Workstream (Epic-equivalent): {0}" -f $epicKey)
Log 'Created Features (Task issue type):'
$featureKeys.GetEnumerator() | Sort-Object Name | ForEach-Object { Log ("- {0}: {1}" -f $_.Value, $_.Key) }
Log 'Created User Stories (Sub-task issue type):'
$createdStories | ForEach-Object { Log ("- {0}" -f $_) }
Log 'DONE'
}
catch {
    Log ('ERROR: ' + $_.Exception.Message)
    if ($_.ScriptStackTrace) {
        Log ('STACK: ' + $_.ScriptStackTrace)
    }
    exit 1
}
