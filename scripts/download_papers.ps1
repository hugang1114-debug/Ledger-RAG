param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$paperDir = Join-Path $repoRoot "literature\papers"
New-Item -ItemType Directory -Force -Path $paperDir | Out-Null

$papers = @(
    @{
        id = "rag_original"
        file = "2020_rag_neurips.pdf"
        url = "https://proceedings.neurips.cc/paper_files/paper/2020/file/6b493230205f780e1bc26945df7481e5-Paper.pdf"
    },
    @{
        id = "gophercite"
        file = "2022_gophercite_arxiv.pdf"
        url = "https://arxiv.org/pdf/2203.11147.pdf"
    },
    @{
        id = "attributed_qa"
        file = "2022_attributed-qa_arxiv.pdf"
        url = "https://arxiv.org/pdf/2212.08037.pdf"
    },
    @{
        id = "alce"
        file = "2023_alce_acl.pdf"
        url = "https://aclanthology.org/2023.emnlp-main.398.pdf"
    },
    @{
        id = "self_rag"
        file = "2024_self-rag_iclr.pdf"
        url = "https://proceedings.iclr.cc/paper_files/paper/2024/file/25f7be9694d7b32d5cc670927b8091e1-Paper-Conference.pdf"
    },
    @{
        id = "crag"
        file = "2024_crag_arxiv.pdf"
        url = "https://arxiv.org/pdf/2401.15884.pdf"
    },
    @{
        id = "lost_in_the_middle"
        file = "2024_lost-in-the-middle_tacl.pdf"
        url = "https://aclanthology.org/2024.tacl-1.9.pdf"
    },
    @{
        id = "expertqa"
        file = "2024_expertqa_naacl.pdf"
        url = "https://aclanthology.org/2024.naacl-long.167.pdf"
    },
    @{
        id = "longbench"
        file = "2024_longbench_acl.pdf"
        url = "https://aclanthology.org/2024.acl-long.172.pdf"
    },
    @{
        id = "longcite"
        file = "2025_longcite_acl-findings.pdf"
        url = "https://aclanthology.org/2025.findings-acl.264.pdf"
    },
    @{
        id = "aliice"
        file = "2025_aliice_naacl.pdf"
        url = "https://aclanthology.org/2025.naacl-long.23.pdf"
    },
    @{
        id = "l_citeeval"
        file = "2025_l-citeeval_acl.pdf"
        url = "https://aclanthology.org/2025.acl-long.263.pdf"
    },
    @{
        id = "sunset"
        file = "2025_sunset_emnlp.pdf"
        url = "https://aclanthology.org/2025.emnlp-main.95.pdf"
    },
    @{
        id = "trace"
        file = "2025_trace_arxiv.pdf"
        url = "https://arxiv.org/pdf/2505.13258.pdf"
    },
    @{
        id = "nolima"
        file = "2025_nolima_openreview.pdf"
        url = "https://openreview.net/pdf?id=0OshX1hiSa"
    },
    @{
        id = "loca_bench"
        file = "2026_loca-bench_arxiv.pdf"
        url = "https://arxiv.org/pdf/2602.07962.pdf"
    },
    @{
        id = "agentic_context_engineering"
        file = "2025_agentic-context-engineering_arxiv.pdf"
        url = "https://arxiv.org/pdf/2510.04618.pdf"
    },
    @{
        id = "citeme"
        file = "2024_citeme_arxiv.pdf"
        url = "https://arxiv.org/pdf/2407.12861.pdf"
    },
    @{
        id = "citeguard"
        file = "2025_citeguard_arxiv.pdf"
        url = "https://arxiv.org/pdf/2510.17853.pdf"
    }
)

$results = @()

foreach ($paper in $papers) {
    $target = Join-Path $paperDir $paper.file
    $status = "downloaded"
    $errorMessage = $null

    try {
        if ((Test-Path -LiteralPath $target) -and -not $Force) {
            $status = "already_present"
        } else {
            Invoke-WebRequest -Uri $paper.url -OutFile $target -MaximumRedirection 5 -Headers @{ "User-Agent" = "Ledger-RAG literature setup" }
        }

        $hash = Get-FileHash -LiteralPath $target -Algorithm SHA256
        $item = Get-Item -LiteralPath $target
        $results += [pscustomobject]@{
            id = $paper.id
            status = $status
            file = $paper.file
            bytes = $item.Length
            sha256 = $hash.Hash.ToLowerInvariant()
            url = $paper.url
            error = $errorMessage
        }
    } catch {
        $results += [pscustomobject]@{
            id = $paper.id
            status = "failed"
            file = $paper.file
            bytes = 0
            sha256 = ""
            url = $paper.url
            error = $_.Exception.Message
        }
    }
}

$results | ConvertTo-Json -Depth 4

