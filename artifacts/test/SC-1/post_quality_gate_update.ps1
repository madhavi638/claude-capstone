$ErrorActionPreference = 'Stop'

$envFile = 'c:/Users/MadhaviRambha/STLC-CapstoneProject/env/api-jira.env'
Get-Content $envFile | ForEach-Object {
    if (-not ($_ -match '^\s*#' -or $_ -match '^\s*$')) {
        $parts = $_ -split '=', 2
        if ($parts.Count -eq 2) {
            [Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), 'Process')
        }
    }
}

$base = $env:JIRA_BASE_URL.TrimEnd('/')
$pair = ('{0}:{1}' -f $env:JIRA_EMAIL, $env:JIRA_API_TOKEN)
$basic = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
$headers = @{
    Authorization = ('Basic {0}' -f $basic)
    Accept = 'application/json'
    'Content-Type' = 'application/json'
}

$commentText = @'
Quality Gate Result: PASS
Pass Rate: 100%
Coverage: 100%
Defect Summary: 0 defects, 0 blockers, 0 failed tests
Release Recommendation: Release Approved
Final Decision: PASS

Evidence:
- artifacts/test/SC-1/QUALITY_GATE_REPORT_SC-1.md
- artifacts/test/SC-1/DEFECT_ANALYSIS_SC-1.md
- artifacts/test/SC-1/EXECUTION_SUMMARY_SC-1.md
'@

$payload = @{
    body = @{
        type = 'doc'
        version = 1
        content = @(
            @{
                type = 'paragraph'
                content = @(
                    @{
                        type = 'text'
                        text = $commentText
                    }
                )
            }
        )
    }
} | ConvertTo-Json -Depth 20

Invoke-RestMethod -Uri "$base/rest/api/3/issue/SC-1/comment" -Headers $headers -Method Post -Body $payload | Out-Null
Write-Output 'JIRA_COMMENT_POSTED_SC-1'
