$ErrorActionPreference = 'Stop'

$owner = 'madhavi638'
$repo = 'STLC_CapstoneAI'
$ticketId = 'SC-1'
$sourceBranch = 'feature/SC-1'
$targetBranch = 'main'
$title = "$ticketId - Test Automation Delivery Package"

if (-not $env:GITHUB_TOKEN) {
    throw 'GITHUB_TOKEN is not set in the current process environment.'
}

$headers = @{
    Authorization = "Bearer $($env:GITHUB_TOKEN)"
    Accept = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2022-11-28'
}

$headParam = [uri]::EscapeDataString("${owner}:$sourceBranch")
$existingUri = "https://api.github.com/repos/$owner/$repo/pulls?state=all&head=$headParam&base=$targetBranch"
$existing = Invoke-RestMethod -Method Get -Uri $existingUri -Headers $headers
if ($existing.Count -gt 0) {
    $pr = $existing | Select-Object -First 1
    $result = [ordered]@{
        number = $pr.number
        url = $pr.html_url
        title = $pr.title
        head = $pr.head.ref
        base = $pr.base.ref
        state = $pr.state
        reusedExisting = $true
    }
    $result | ConvertTo-Json -Depth 5
    exit 0
}

$body = @(
    'Summary of test deliverables for SC-1 has been assembled and validated.'
    ''
    '- Tests run: 18'
    '- Passed: 18'
    '- Failed: 0'
    '- Quality Gate: PASS'
    '- Review Readiness: READY'
    ''
    'Primary artifacts are under artifacts/test/SC-1, including tests, test data, execution reports, and quality/verification reports.'
) -join "`n"

$payload = @{
    title = $title
    head = $sourceBranch
    base = $targetBranch
    body = $body
} | ConvertTo-Json -Depth 5

$pr = Invoke-RestMethod -Method Post -Uri "https://api.github.com/repos/$owner/$repo/pulls" -Headers $headers -Body $payload -ContentType 'application/json'

$labelsPayload = @{ labels = @('test', 'automation', 'verification') } | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post -Uri "https://api.github.com/repos/$owner/$repo/issues/$($pr.number)/labels" -Headers $headers -Body $labelsPayload -ContentType 'application/json' | Out-Null

$result = [ordered]@{
    number = $pr.number
    url = $pr.html_url
    title = $pr.title
    head = $pr.head.ref
    base = $pr.base.ref
    state = $pr.state
    reusedExisting = $false
}

$result | ConvertTo-Json -Depth 5
