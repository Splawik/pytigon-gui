#!/usr/bin/env bash
# =============================================================================
# gen_docs.sh – Generate pytigon_gui API documentation with MkDocs + mkdocstrings
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MKDOCS_DIR="$SCRIPT_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${CYAN}[STEP]${NC}  $*"; }

install_deps() {
    log_step "Installing MkDocs + Material + mkdocstrings..."
    PIP="pip3"; command -v pip3 &>/dev/null || PIP="pip"
    $PIP install --upgrade mkdocs mkdocs-material "mkdocstrings[python]" mkdocs-material-extensions pymdown-extensions
    log_info "Done. Run: ./gen_docs.sh serve"
}

check_deps() {
    command -v mkdocs &>/dev/null || { log_error "mkdocs not found. Run install first."; exit 1; }
    python3.13 -c "import mkdocstrings" 2>/dev/null || { log_error "mkdocstrings not found."; exit 1; }
}

build_docs() {
    check_deps; log_step "Building..."
    cd "$MKDOCS_DIR"
    mkdocs build --config-file "$MKDOCS_DIR/mkdocs.yml" --clean
    [[ -d "$MKDOCS_DIR/site" ]] && log_info "Built: $MKDOCS_DIR/site/" || { log_error "Build failed."; exit 1; }
}

serve_docs() {
    check_deps; log_step "Serving at http://127.0.0.1:8000 ..."
    cd "$MKDOCS_DIR"
    mkdocs serve --config-file "$MKDOCS_DIR/mkdocs.yml" --dev-addr 127.0.0.1:8000
}

clean_docs() {
    [[ -d "$MKDOCS_DIR/site" ]] && { rm -rf "$MKDOCS_DIR/site"; log_info "Cleaned."; } || log_info "Nothing to clean."
}

deploy_docs() {
    check_deps; log_step "Deploying..."
    cd "$MKDOCS_DIR"
    mkdocs gh-deploy --config-file "$MKDOCS_DIR/mkdocs.yml" --force
    log_info "Deployed."
}

case "${1:-build}" in
    install) install_deps ;;
    build)   build_docs ;;
    serve)   serve_docs ;;
    clean)   clean_docs ;;
    deploy)  deploy_docs ;;
    *) echo "Usage: $0 {build|serve|clean|install|deploy}"; exit 1 ;;
esac
