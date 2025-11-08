import re, json, socket, ipaddress, requests, tldextract
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Tuple

# ---------- URL utils ----------

BARE_URL_RX = re.compile(r'(?:(?:https?://)?(?:www\.)?[A-Za-z0-9.-]+\.[A-Za-z]{2,})(?:/[^\s<>"\)]*)?', re.I)
HTTP_URL_RX = re.compile(r'https?://[^\s<>"\)]+', re.I)

def normalize_url(raw: str) -> str | None:
    raw = (raw or "").strip().strip("<>")
    if not raw: return None
    if not raw.startswith(("http://","https://")):
        # treat bare domains as https by default
        raw = "https://" + raw
    p = urlparse(raw)
    if p.scheme not in ("http","https"): 
        return None
    # drop fragments
    p = p._replace(fragment="")
    return urlunparse(p)

def extract_urls_from_text(text: str) -> List[str]:
    # prefer explicit http(s) matches; fallback to bare domains
    urls = HTTP_URL_RX.findall(text or "")
    if not urls:
        urls = BARE_URL_RX.findall(text or "")
    # normalize & dedupe
    n = []
    seen = set()
    for u in urls:
        nu = normalize_url(u)
        if nu and nu not in seen:
            seen.add(nu); n.append(nu)
    return n

# ---------- Network guards & DNS ----------

def resolve_public_ips(host: str) -> Tuple[bool, List[str], str | None]:
    """Resolve host; ensure IPs are public (not private/loopback/link-local)."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        return False, [], f"dns_failure:{e}"
    ips = sorted({i[4][0] for i in infos})
    try:
        for ip in ips:
            ipobj = ipaddress.ip_address(ip)
            if (ipobj.is_private or ipobj.is_loopback or ipobj.is_link_local or
                ipobj.is_reserved or ipobj.is_multicast):
                return False, ips, f"non_public_ip:{ip}"
    except ValueError:
        return False, ips, "ip_parse_error"
    return True, ips, None

# ---------- Fetch & classify ----------

def fetch_page(url: str, timeout: float = 10.0) -> Dict[str, Any]:
    s = requests.Session()
    s.headers.update({"User-Agent": "TL-Verifier/1.0 (+evidence-check)"})
    # HEAD first, fall back to GET
    try:
        h = s.head(url, allow_redirects=True, timeout=timeout)
        final = h.url
        ct = (h.headers.get("Content-Type","") or "").split(";")[0].lower()
        status = h.status_code
        text = ""
        if "text/html" in ct or not ct:
            g = s.get(final, allow_redirects=True, timeout=timeout)
            final = g.url or final
            status = g.status_code or status
            ct = (g.headers.get("Content-Type","") or ct).split(";")[0].lower()
            text = g.text if "text/html" in (ct or "") else ""
        elif ct == "application/pdf":
            # don’t download the whole file — consider it a “document”
            text = ""
        return {"ok": status < 400, "status": status, "final_url": final, "content_type": ct, "html": text}
    except requests.exceptions.SSLError:
        return {"ok": False, "error": "tls_error"}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "timeout"}
    except requests.RequestException as e:
        return {"ok": False, "error": f"http_error:{type(e).__name__}"}

SCHEMA_TO_CATEGORY = {
    "NewsArticle":"news", "Article":"article", "BlogPosting":"blog",
    "ScholarlyArticle":"education", "TechArticle":"docs",
    "Report":"report", "VideoObject":"video", "FAQPage":"docs",
    "QAPage":"qna", "ProfilePage":"profile", "Product":"ecommerce",
    "Organization":"org", "WebSite":"website", "WebPage":"website"
}

def parse_jsonld_types(html: str) -> List[str]:
    types = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(tag.string or "")
                objs = data if isinstance(data, list) else [data]
                for obj in objs:
                    t = obj.get("@type")
                    if isinstance(t, list): types += [str(x).lower() for x in t]
                    elif isinstance(t, str): types.append(t.lower())
            except Exception:
                continue
    except Exception:
        pass
    return list(set(types))

def guess_category(final_url: str, content_type: str, html: str) -> Tuple[str, float, Dict[str, Any]]:
    """Return (category, confidence, signals). No domain list; rely on page/TLD signals."""
    signals = {}
    if content_type == "application/pdf":
        return "document/pdf", 0.95, {"content_type":"pdf"}
    if "text/html" not in (content_type or ""):
        return "website", 0.5, {"content_type":content_type or "unknown"}

    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string or "").strip() if soup.title else ""
    og_type = soup.find("meta", property="og:type")
    og_type = (og_type.get("content","").strip().lower() if og_type else "")

    # TLD cues (.gov/.edu)
    domain = tldextract.extract(final_url).registered_domain or ""
    suffix = tldextract.extract(final_url).suffix or ""
    if suffix.endswith("gov") or suffix.endswith("gov.uk"):
        return "government", 0.9, {"tld":"gov"}
    if suffix.endswith("edu"):
        return "education", 0.85, {"tld":"edu"}

    # JSON-LD types
    jl = parse_jsonld_types(html)
    mapped = [SCHEMA_TO_CATEGORY.get(t.capitalize(), "") for t in jl]
    mapped = [m for m in mapped if m]
    if mapped:
        # choose a higher-value type if present
        priority = ["education","news","report","docs","blog","article","video","qna","ecommerce","website","org","profile"]
        for p in priority:
            if p in mapped:
                signals["jsonld"] = mapped
                base = 0.88 if p in {"education","news","report","docs"} else 0.8
                return p, base, signals

    # OpenGraph hints
    if og_type:
        signals["og:type"] = og_type
        if "video" in og_type: return "video", 0.8, signals
        if og_type in {"article"}: return "article", 0.7, signals
        if "profile" in og_type: return "profile", 0.75, signals

    # Path/content hints
    path = urlparse(final_url).path.lower()
    text = soup.get_text(" ", strip=True).lower()
    if any(k in path for k in ("/docs","/documentation","/api","/developer")):
        return "docs", 0.7, {"path_hint":"docs"}
    if "add to cart" in text or "sku" in text or "/product" in path:
        return "ecommerce", 0.7, {"content_hint":"product"}

    # Fallback
    return "website", 0.55, {"fallback":"generic"}

def verify_and_classify(url: str) -> Dict[str, Any]:
    """Real-time verification + classification. No local credibility list."""
    out = {
        "input_url": url, "normalized_url": None, "final_url": None,
        "domain": None, "ips": [], "public_dns_ok": None, "http_ok": None,
        "status": None, "content_type": None, "category": None, "confidence": 0.0,
        "verified": False, "reason": None, "signals": {}
    }
    nu = normalize_url(url)
    if not nu:
        out["reason"] = "bad_scheme_or_parse"
        return out
    out["normalized_url"] = nu
    host = urlparse(nu).hostname or ""
    out["domain"] = tldextract.extract(host).registered_domain or host

    # DNS & public IP check
    dns_ok, ips, dns_err = resolve_public_ips(host)
    out["ips"] = ips
    if not dns_ok:
        out["public_dns_ok"] = False
        out["reason"] = dns_err or "dns_failure"
        return out
    out["public_dns_ok"] = True

    # Fetch page
    fetched = fetch_page(nu)
    if not fetched.get("ok", False):
        out["http_ok"] = False
        out["reason"] = fetched.get("error") or f"http_status_{fetched.get('status')}"
        out["status"] = fetched.get("status")
        return out

    out["http_ok"] = True
    out["status"] = fetched["status"]
    out["final_url"] = fetched["final_url"]
    out["content_type"] = fetched["content_type"]

    # Classify by reading the front page
    cat, conf, signals = guess_category(out["final_url"], out["content_type"], fetched.get("html",""))
    out["category"], out["confidence"], out["signals"] = cat, conf, signals

    # Verdict: Verified if DNS ok + HTTP ok (<400) + looks like content
    if out["public_dns_ok"] and out["http_ok"] and out["status"] and out["status"] < 400:
        out["verified"] = True
        out["reason"] = "reachable"
    else:
        out["verified"] = False
        out["reason"] = out["reason"] or "unreachable"
    return out

# ---------- Per-comment pipeline ----------

def analyze_comment(comment_id: str, text: str) -> Dict[str, Any]:
    urls = extract_urls_from_text(text)
    link_results = [verify_and_classify(u) for u in urls]
    # Summarize comment-level status
    if not link_results:
        status = "None"
    else:
        # Verified if any link verified; Mixed if some verified and some not; else Unverified
        v = sum(1 for r in link_results if r["verified"])
        if v == len(link_results):
            status = "Verified"
        elif v > 0:
            status = "Mixed"
        else:
            status = "Unverified"
    # TL2/TL3 style strings without domain lists
    if status == "Verified":
        tl2 = "Verified source"
        tl3 = f"Verified: {', '.join(sorted({r['category'] for r in link_results if r['verified']}))}"
    elif status == "Mixed":
        tl2 = "Mixed evidence"
        tl3 = f"Mixed: {sum(r['verified'] for r in link_results)} verified, {sum(not r['verified'] for r in link_results)} unverified"
    elif status == "Unverified":
        tl2 = "Unverified source ⚠️"
        tl3 = "Unverified: links unreachable or error"
    else:
        tl2 = "No evidence detected"
        tl3 = "Opinion only; no evidence detected"
    return {
        "comment_id": comment_id,
        "text": text,
        "urls": urls,
        "status": status,
        "results": link_results,
        "TL2_tooltip": tl2,
        "TL3_detail": tl3
    }

def analyze_comments(comments: List[Dict[str,str]]) -> List[Dict[str,Any]]:
    return [analyze_comment(c["comment_id"], c["text"]) for c in comments]
