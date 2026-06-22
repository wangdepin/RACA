"""Guard: refuse to run compute-heavy commands on a cluster LOGIN node.

``raca ssh <cluster> "<cmd>"`` executes ``<cmd>`` directly on the login node
(see ``ssh_session.SSHSessionManager._run_mux``). Heavy compute — alignment,
``samtools`` over BAMs, big sorts/hashes of genomics files — belongs on a
COMPUTE node via ``srun``/``sbatch``. Cluster admins flag login-node workloads
because they clog the shared front-end.

This module inspects a command string and decides whether it is safe to run on
a login node. The policy is intentionally aggressive — when in doubt about a
known compute tool, block — but it never breaks the workflows that *must* run
on the login node (job submission and network/download/install, since compute
nodes have no internet).

Policy
------
ALLOW on the login node:
  * SLURM control & submission (``squeue``/``sacct``/``srun``/``sbatch`` …) —
    these are the control plane and how work reaches compute nodes.
  * Network / transfer / install tools (``sracha``/``wget``/``rsync``/``pip`` …)
    — low CPU, and compute nodes have no internet.
  * Lightweight shell & file utilities (``ls``/``cat``/``mkdir``/``awk`` on a
    small text file …).
  * Anything unknown — custom scripts are usually orchestration wrappers that
    belong on the login node; we don't guess them heavy.

BLOCK on the login node (must go to a compute node):
  * Known compute-heavy programs (``samtools``/``STAR``/``bwa``/``cellranger`` …).
  * Text-processing tools (``awk``/``sort``/``md5sum``/``python`` …) when the
    command references a large genomics file (``.bam``/``.cram``/``.fastq.gz`` …).

Override: pass ``allow_login=True`` (``raca ssh --allow-login``) or export
``RACA_ALLOW_LOGIN=1`` for a command you know is trivial.
"""

from __future__ import annotations

import os
import re

# --- Command classes -------------------------------------------------------

# Job submission — the command runs ON a compute node, so always allowed and we
# do not inspect its payload.
COMPUTE_OK = frozenset({"srun", "sbatch", "salloc", "sattach"})

# SLURM control plane — must run on the login node.
CONTROL_OK = frozenset({
    "squeue", "sacct", "sinfo", "scontrol", "scancel", "sstat", "sprio",
    "sshare", "sacctmgr", "sbcast", "sgather", "sdiag", "seff", "sreport",
    "scrontab", "sview", "sbatch", "srun", "salloc",
})

# Network / transfer / install — must run on the login node (no internet on
# compute nodes). Low CPU.
NETWORK_OK = frozenset({
    "sracha", "prefetch", "fasterq-dump", "fastq-dump", "sam-dump",
    "vdb-config", "vdb-validate", "wget", "wget2", "curl", "aria2c", "axel",
    "rsync", "scp", "sftp", "lftp", "ftp", "git", "git-lfs", "pip", "pip3",
    "pipx", "conda", "mamba", "micromamba", "pixi", "poetry", "uv",
    "huggingface-cli", "hf", "datasets-cli", "aws", "gcloud", "gsutil", "gh",
    "rclone", "s5cmd", "wandb", "dvc",
})

# Lightweight shell / file utilities — cheap on the login node.
LIGHT_OK = frozenset({
    "ls", "cat", "echo", "printf", "pwd", "cd", "mkdir", "rmdir", "rm", "cp",
    "mv", "ln", "touch", "stat", "test", "[", "[[", "true", "false", ":",
    "df", "du", "head", "tail", "wc", "hostname", "uname", "whoami", "id",
    "groups", "which", "command", "type", "hash", "realpath", "dirname",
    "basename", "readlink", "date", "printenv", "export", "set", "unset",
    "source", ".", "alias", "sleep", "kill", "jobs", "tmux", "screen",
    "clear", "tput", "mktemp", "mkfifo", "getconf", "ulimit", "free",
    "uptime", "w", "who", "last", "ps", "pgrep", "pkill", "chmod", "chown",
    "chgrp", "file", "tree", "tee", "yes", "seq", "expr", "let", "bc",
    "column", "look", "cmp", "diff", "find", "ssh", "exit", "return",
})

# Compute-heavy programs — block on the login node unconditionally.
HEAVY_BINARIES = frozenset({
    # SAM/BAM/VCF processing
    "samtools", "bcftools", "bedtools", "vcftools", "bamtools", "sambamba",
    # aligners / quantifiers
    "STAR", "STARsolo", "hisat2", "hisat2-build", "hisat-3n", "bwa",
    "bwa-mem2", "bowtie", "bowtie2", "bowtie2-build", "tophat", "tophat2",
    "salmon", "kallisto", "minimap2", "gmap", "gsnap", "subread-align",
    "subjunc", "featureCounts", "htseq-count", "stringtie", "cufflinks",
    "cuffdiff", "rsem-calculate-expression", "rsem-prepare-reference",
    "star-fusion", "arriba",
    # QC / trimming
    "fastqc", "fastp", "cutadapt", "trim_galore", "trimmomatic", "multiqc",
    # single cell
    "cellranger", "spaceranger", "cellranger-atac", "alevin", "alevin-fry",
    "kb", "bustools", "umi_tools",
    # variant calling
    "gatk", "gatk4", "picard", "freebayes", "deepvariant", "vardict",
    "strelka", "manta", "varscan", "lofreq",
    # coverage / signal / peaks
    "deeptools", "bamCoverage", "bamCompare", "multiBamSummary",
    "computeMatrix", "plotHeatmap", "macs2", "macs3", "genrich", "homer",
    # assembly
    "spades.py", "megahit", "Trinity", "canu", "flye", "wtdbg2", "racon",
    "medaka",
    # search / clustering
    "blastn", "blastp", "blastx", "tblastn", "makeblastdb", "diamond",
    "hmmsearch", "hmmscan", "jackhmmer", "mmseqs", "vsearch", "usearch",
    "cd-hit",
    # alignment / phylo
    "mafft", "muscle", "clustalo", "raxml", "raxml-ng", "iqtree", "iqtree2",
    "fasttree",
})

# Text/data processing tools — block only when the command also references a
# large genomics file (see HEAVY_EXT). Otherwise they're fine on small inputs.
PROCESSING_TOOLS = frozenset({
    "awk", "gawk", "mawk", "sed", "grep", "egrep", "fgrep", "zgrep", "rg",
    "sort", "cut", "tr", "uniq", "comm", "join", "paste", "split", "csplit",
    "tac", "fold", "fmt", "nl", "rev", "zcat", "gzip", "gunzip", "bzip2",
    "bunzip2", "bzcat", "xz", "unxz", "xzcat", "zstd", "unzstd", "zstdcat",
    "pigz", "unpigz", "lz4", "md5sum", "sha1sum", "sha224sum", "sha256sum",
    "sha384sum", "sha512sum", "b2sum", "cksum", "sum", "python", "python2",
    "python3", "Rscript", "R", "julia", "perl", "ruby", "node", "java",
    "octave",
})

# Large genomics file extensions that mark a processing command as heavy.
HEAVY_EXT = (
    ".bam", ".sam", ".cram", ".bcf", ".h5ad", ".loom", ".mtx", ".npy",
    ".npz", ".bigwig", ".bigbed", ".2bit", ".fastq.gz", ".fq.gz", ".fastq",
    ".fq",
)
_HEAVY_EXT_RE = re.compile(
    "(?i)(?:" + "|".join(re.escape(e) for e in HEAVY_EXT) + r")(?![A-Za-z0-9])"
)

# Wrappers we look *through* to find the real command.
_RUNNERS = frozenset({"pixi", "conda", "mamba", "micromamba", "poetry", "uv"})
_WRAPPERS = frozenset({
    "nohup", "time", "nice", "ionice", "stdbuf", "timeout", "xargs",
    "setsid", "eatmydata", "chrt",
})
_SHELLS = frozenset({"bash", "sh", "zsh", "dash", "ksh"})
_VALUE_FLAGS = frozenset({
    "--manifest-path", "-e", "--environment", "-n", "--name", "-p",
    "--prefix", "-C", "--directory",
})

_OP_CHARS = set("|&;<>()")
_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


# --- Tokenization ----------------------------------------------------------

def _tokenize(command: str) -> list[str]:
    """Split a shell command into word and operator tokens, respecting quotes."""
    tokens: list[str] = []
    cur: list[str] = []
    i, n = 0, len(command)

    def flush() -> None:
        if cur:
            tokens.append("".join(cur))
            cur.clear()

    while i < n:
        c = command[i]
        if c in ("'", '"'):
            quote = c
            i += 1
            while i < n and command[i] != quote:
                cur.append(command[i])
                i += 1
            i += 1  # closing quote
            continue
        if c == "\\" and i + 1 < n:
            cur.append(command[i + 1])
            i += 2
            continue
        if c.isspace():
            flush()
            i += 1
            continue
        if c in _OP_CHARS:
            flush()
            j = i
            while j < n and command[j] in _OP_CHARS:
                j += 1
            tokens.append(command[i:j])
            i = j
            continue
        cur.append(c)
        i += 1
    flush()
    return tokens


def _simple_commands(command: str) -> list[list[str]]:
    """Break a command into simple commands, split at shell operators."""
    cmds: list[list[str]] = []
    cur: list[str] = []
    for tok in _tokenize(command):
        if tok and all(ch in _OP_CHARS for ch in tok):
            if cur:
                cmds.append(cur)
                cur = []
        else:
            cur.append(tok)
    if cur:
        cmds.append(cur)
    return cmds


def _basename(token: str) -> str:
    return token.rsplit("/", 1)[-1]


def _is_assignment(token: str) -> bool:
    return bool(_ASSIGN_RE.match(token))


def _skip_options(tokens: list[str]) -> list[str]:
    """Drop leading option flags (and the values of known value-flags)."""
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if not t.startswith("-"):
            break
        if t in _VALUE_FLAGS and i + 1 < len(tokens):
            i += 2
        else:
            i += 1
    return tokens[i:]


def _resolve_heads(tokens: list[str], depth: int = 0) -> list[str]:
    """Return the effective command head name(s) after unwrapping wrappers.

    ``env``/assignments, ``pixi run``/``conda run``, ``nohup``/``timeout`` and
    ``bash -c "<inner>"`` are looked through so the *real* program is classified.
    """
    if depth > 8 or not tokens:
        return []

    i = 0
    while i < len(tokens) and _is_assignment(tokens[i]):
        i += 1
    tokens = tokens[i:]
    if not tokens:
        return []

    base = _basename(tokens[0])

    if base in _SHELLS and "-c" in tokens:
        ci = tokens.index("-c")
        heads: list[str] = []
        if ci + 1 < len(tokens):
            for sc in _simple_commands(tokens[ci + 1]):
                heads += _resolve_heads(sc, depth + 1)
        return heads or [base]

    if base in _RUNNERS:
        rest = tokens[1:]
        if rest and rest[0] in ("run", "exec", "r"):
            rest = rest[1:]
        rest = _skip_options(rest)
        return _resolve_heads(rest, depth + 1) or [base]

    if base in _WRAPPERS:
        rest = _skip_options(tokens[1:])
        if base == "timeout" and rest:
            rest = rest[1:]  # drop the duration positional
        return _resolve_heads(rest, depth + 1) or [base]

    if base == "env":
        rest = tokens[1:]
        k = 0
        while k < len(rest):
            t = rest[k]
            if t == "-i":
                k += 1
            elif t == "-u" and k + 1 < len(rest):
                k += 2
            elif _is_assignment(t):
                k += 1
            else:
                break
        return _resolve_heads(rest[k:], depth + 1) or [base]

    return [base]


def _references_heavy_file(command: str) -> bool:
    return bool(_HEAVY_EXT_RE.search(command))


# --- Public API ------------------------------------------------------------

def classify(command: str) -> tuple[str | None, str]:
    """Classify a command.

    Returns ``(offending_head, reason)`` if the command must NOT run on a login
    node, else ``(None, "")``.
    """
    refs_heavy = _references_heavy_file(command)
    for sc in _simple_commands(command):
        for head in _resolve_heads(sc):
            if head in COMPUTE_OK or head in CONTROL_OK or head in NETWORK_OK:
                continue
            if head in HEAVY_BINARIES:
                return head, f"'{head}' is a compute-heavy program"
            if head in PROCESSING_TOOLS and refs_heavy:
                return head, f"'{head}' is processing large genomics data"
            # LIGHT_OK or unknown → allowed
    return None, ""


def _env_override() -> bool:
    return os.environ.get("RACA_ALLOW_LOGIN", "").strip().lower() in (
        "1", "true", "yes", "on",
    )


def check_login_command(
    command: str, cluster: str = "<cluster>", allow_login: bool = False
) -> str | None:
    """Return a block message if ``command`` is unsafe on a login node, else None."""
    if allow_login or _env_override():
        return None
    head, why = classify(command)
    if head is None:
        return None
    return (
        f"ERROR: refusing to run a compute-heavy command on the {cluster} "
        f"LOGIN node.\n"
        f"  Triggered by: {head} ({why}).\n"
        f"  `raca ssh` runs commands directly on the login node — heavy compute "
        f"must run on a COMPUTE node.\n"
        f"  Do one of:\n"
        f'    - srun:   raca ssh {cluster} "srun -p short -c 8 --mem=16G '
        f'-t 02:00:00 <command>"\n'
        f'    - sbatch: raca ssh {cluster} "sbatch <job>.sh"\n'
        f'    - if this really is trivial: '
        f'raca ssh --allow-login {cluster} "<command>"'
    )
