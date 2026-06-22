"""Tests for the login-node compute guard (raca.login_guard)."""

from __future__ import annotations

import pytest

from raca.login_guard import check_login_command, classify

# Commands that MUST be allowed to run on the login node.
ALLOWED = [
    # SLURM control plane + submission
    "squeue -u depinwan",
    "sacct -j 75014075 --format=JobID,State,Elapsed",
    "sbatch run_cellranger_array.sbatch",
    "sbatch --test-only --partition=short --wrap='hostname'",
    "scancel 12345",
    "sinfo -p short",
    # job submission that wraps heavy compute → runs on a compute node
    "srun -p short -c 8 --mem=16G samtools view -c x.bam",
    'sbatch --wrap="STAR --runThreadN 8 --genomeDir ref"',
    # network / download / install (no internet on compute nodes)
    "wget https://example.org/ref.fa.gz",
    "pixi run sracha get SRR37210167 --split split-files",
    "prefetch SRR37210167",
    "rsync -av src/ dest/",
    "git pull",
    "pip install --quiet pysam",
    "huggingface-cli upload org/repo .",
    # lightweight shell / file inspection
    "ls -la /wrk-kappa/users/depinwan/tries",
    "mkdir -p logs && cd logs",
    "df --output=avail -BM .",
    "cat runinfo.csv | head -5",
    "wc -l manifest.tsv",
    "echo '--- recovered deduped reads per contig ---'",
    "TMPDIR=/tmp ls -la",
    "./download_all.sh",                       # unknown script → allowed
    # processing tools on small / non-genomics inputs → allowed
    "awk -F'\\t' 'NR>1 {print $1}' manifest.tsv",
    "zcat genes.gtf.gz | awk '$3==\"gene\"'",  # .gtf.gz is not a heavy ext
    "md5sum manifest.tsv",
    "python parse_runinfo.py",                 # no heavy file on the cmdline
    "sort -k1,1 manifest.tsv",
]

# Commands that MUST be refused on the login node.
BLOCKED = [
    # the actual 141h offender class
    "samtools view x.bam | awk '{n=0; c=$6}'",
    "samtools sort -o out.bam in.bam",
    "TMPDIR=/tmp samtools sort in.bam",
    "nohup samtools view big.bam > out.sam",
    "pixi run samtools index x.bam",
    "bash -c 'samtools view x.bam | sort -n'",
    # aligners / quantifiers / single-cell / variant
    "STAR --runThreadN 8 --genomeDir ref --readFilesIn r1.fq r2.fq",
    "bwa mem ref.fa reads.fq",
    "cellranger count --id=run1 --fastqs=fq",
    "umi_tools dedup -I in.bam -S out.bam",
    "gatk HaplotypeCaller -I in.bam -O out.vcf",
    "featureCounts -a genes.gtf -o counts.txt in.bam",
    # processing tools touching large genomics files
    "md5sum GSM9515541_R1.fastq.gz",
    "zcat reads.fastq.gz | awk '{print}'",
    "sort -k1 big.cram",
    "python crunch.py sample.h5ad",
]


@pytest.mark.parametrize("cmd", ALLOWED)
def test_allowed_commands_pass(cmd):
    head, _ = classify(cmd)
    assert head is None, f"expected ALLOW but blocked on {head!r}: {cmd}"
    assert check_login_command(cmd, cluster="turso") is None


@pytest.mark.parametrize("cmd", BLOCKED)
def test_blocked_commands_refused(cmd):
    head, reason = classify(cmd)
    assert head is not None, f"expected BLOCK but allowed: {cmd}"
    msg = check_login_command(cmd, cluster="turso")
    assert msg is not None and "LOGIN node" in msg


def test_allow_login_flag_overrides():
    cmd = "samtools view x.bam"
    assert classify(cmd)[0] == "samtools"
    assert check_login_command(cmd, cluster="turso", allow_login=True) is None


def test_env_override(monkeypatch):
    monkeypatch.setenv("RACA_ALLOW_LOGIN", "1")
    assert check_login_command("samtools view x.bam", cluster="turso") is None
