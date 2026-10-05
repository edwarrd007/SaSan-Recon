import base64
import ipaddress
import json
import re

from urllib.parse import urlsplit, urlunsplit


class AssetAnalyzer:

    # ========================================================
    # REGEX
    # ========================================================

    DOMAIN_LABEL_RE = re.compile(
        r"^(?=.{1,63}$)"
        r"[A-Za-z0-9]"
        r"(?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
    )

    SECRET_ASSIGN_RE = re.compile(
        r"(?i)\b("
        r"api[_-]?key|"
        r"access[_-]?token|"
        r"auth(?:orization)?|"
        r"secret|"
        r"client[_-]?secret|"
        r"password|"
        r"passwd"
        r")\b"
        r"\s*(?:=|:)\s*"
        r"[\"']?"
        r"([^\"'\s,;]+)"
    )

    BEARER_RE = re.compile(
        r"(?i)\bBearer\s+"
        r"([A-Za-z0-9._~+/=-]{8,})"
    )

    # ========================================================
    # PLACEHOLDERS
    # ========================================================

    PLACEHOLDER_VALUES = {
        "password",
        "passwd",
        "secret",
        "apikey",
        "api_key",
        "token",
        "changeme",
        "change_me",
        "your_key",
        "your_api_key",
        "example",
        "test",
        "null",
        "none",
        "undefined",
        "xxxxx",
        "xxxxxx",
        "<secret>",
        "<token>",
        "<password>",
    }

    # ========================================================
    # COMMON SUFFIXES
    # ========================================================

    COMMON_MULTI_LABEL_SUFFIXES = {
        "co.uk",
        "org.uk",
        "ac.uk",
        "gov.uk",
        "com.au",
        "net.au",
        "org.au",
        "co.nz",
        "com.br",
        "com.tr",
        "co.jp",
        "com.cn",
        "com.sg",
        "co.in",
    }

    # ========================================================
    # DOMAIN
    # ========================================================

    @staticmethod
    def normalize_domain(
        value: str
    ) -> str | None:

        if not isinstance(
            value,
            str
        ):
            return None

        value = (
            value
            .strip()
            .lower()
            .rstrip(".")
        )

        if not value:
            return None

        # URL accidentally detected as domain
        if "://" in value:

            try:

                parsed = urlsplit(value)

                value = (
                    parsed.hostname
                    or ""
                )

            except Exception:
                return None

        try:

            value = (
                value
                .encode("idna")
                .decode("ascii")
            )

        except Exception:
            return None

        if len(value) > 253:
            return None

        labels = value.split(".")

        if len(labels) < 2:
            return None

        for label in labels:

            if not AssetAnalyzer.DOMAIN_LABEL_RE.match(
                label
            ):
                return None

        return value

    # ========================================================
    # IPv4
    # ========================================================

    @staticmethod
    def validate_ipv4(
        value: str
    ) -> bool:

        try:

            return isinstance(
                ipaddress.ip_address(value),
                ipaddress.IPv4Address
            )

        except ValueError:
            return False

    # ========================================================
    # URL
    # ========================================================

    @staticmethod
    def normalize_url(
        value: str
    ) -> str | None:

        if not isinstance(
            value,
            str
        ):
            return None

        value = value.strip().rstrip(
            ".,);]}"
        )

        try:

            parsed = urlsplit(value)

            if parsed.scheme.lower() not in {
                "http",
                "https",
            }:
                return None

            if not parsed.hostname:
                return None

            host = parsed.hostname.lower()

            try:

                host = (
                    host
                    .encode("idna")
                    .decode("ascii")
                )

            except Exception:
                return None

            # Domain or IP
            if not AssetAnalyzer.normalize_domain(
                host
            ):

                if not AssetAnalyzer.validate_ipv4(
                    host
                ):
                    return None

            scheme = parsed.scheme.lower()

            netloc = host

            if parsed.port is not None:

                if not (
                    (
                        scheme == "http"
                        and parsed.port == 80
                    )
                    or
                    (
                        scheme == "https"
                        and parsed.port == 443
                    )
                ):

                    netloc = (
                        f"{host}:{parsed.port}"
                    )

            return urlunsplit(
                (
                    scheme,
                    netloc,
                    parsed.path,
                    parsed.query,
                    "",
                )
            )

        except Exception:
            return None

    # ========================================================
    # DOMAIN SPLIT
    # ========================================================

    @staticmethod
    def split_domain(
        domain: str
    ):

        domain = (
            AssetAnalyzer.normalize_domain(
                domain
            )
        )

        if not domain:
            return None, None

        labels = domain.split(".")

        if len(labels) == 2:
            return domain, domain

        last_two = ".".join(
            labels[-2:]
        )

        if (
            last_two
            in AssetAnalyzer.COMMON_MULTI_LABEL_SUFFIXES
        ):

            if len(labels) >= 3:

                apex = ".".join(
                    labels[-3:]
                )

            else:

                apex = domain

        else:

            apex = ".".join(
                labels[-2:]
            )

        return domain, apex

    # ========================================================
    # HASH
    # ========================================================

    @staticmethod
    def classify_hash(
        value: str
    ) -> str:

        return {
            32: "MD5",
            40: "SHA1",
            64: "SHA256",
            96: "SHA384",
            128: "SHA512",
        }.get(
            len(value),
            "Unknown"
        )

    @staticmethod
    def analyze_hash(
        value: str
    ) -> dict:

        value = value.strip().lower()

        hash_type = (
            AssetAnalyzer.classify_hash(
                value
            )
        )

        valid = (
            hash_type != "Unknown"
            and re.fullmatch(
                r"[a-f0-9]+",
                value
            ) is not None
        )

        return {
            "value": value,
            "type": hash_type,
            "valid": valid,
            "confidence": (
                0.99
                if valid
                else 0.0
            ),
        }

    # ========================================================
    # JWT
    # ========================================================

    @staticmethod
    def analyze_jwt(
        value: str
    ) -> dict:

        parts = value.split(".")

        result = {
            "value": value,
            "valid_structure": False,
            "header": None,
            "payload": None,
            "algorithm": None,
            "token_type": None,
            "confidence": 0.0,
        }

        if len(parts) != 3:
            return result

        try:

            def decode_segment(
                segment
            ):

                padding = "=" * (
                    -len(segment) % 4
                )

                raw = (
                    base64.urlsafe_b64decode(
                        segment + padding
                    )
                )

                return json.loads(
                    raw.decode("utf-8")
                )

            header = decode_segment(
                parts[0]
            )

            payload = decode_segment(
                parts[1]
            )

            if not isinstance(
                header,
                dict
            ):
                return result

            result["valid_structure"] = True
            result["header"] = header
            result["payload"] = payload
            result["algorithm"] = header.get(
                "alg"
            )
            result["token_type"] = header.get(
                "typ"
            )
            result["confidence"] = 0.99

        except Exception:

            # JWT-like syntax, but decoding failed
            result["confidence"] = 0.45

        return result

    # ========================================================
    # SECRET
    # ========================================================

    @classmethod
    def analyze_secret(
        cls,
        value: str
    ) -> dict:

        value = value.strip()

        matches = []

        for match in cls.SECRET_ASSIGN_RE.finditer(
            value
        ):

            key_name = match.group(1)
            secret_value = match.group(2)

            normalized = (
                secret_value
                .strip()
                .lower()
            )

            is_placeholder = (
                normalized
                in cls.PLACEHOLDER_VALUES
                or normalized.startswith("<")
                or normalized.startswith("${")
                or normalized.startswith("your_")
            )

            entropy_hint = (
                len(secret_value) >= 12
            )

            confidence = 0.55

            if entropy_hint:
                confidence += 0.15

            if not is_placeholder:
                confidence += 0.20

            matches.append(
                {
                    "key": key_name,
                    "value": secret_value,
                    "placeholder": is_placeholder,
                    "confidence": min(
                        confidence,
                        0.99
                    ),
                }
            )

        for match in cls.BEARER_RE.finditer(
            value
        ):

            matches.append(
                {
                    "key": "Authorization",
                    "value": match.group(1),
                    "placeholder": False,
                    "confidence": 0.97,
                }
            )

        if not matches:

            return {
                "value": value,
                "is_secret_candidate": False,
                "confidence": 0.25,
                "matches": [],
            }

        return {
            "value": value,
            "is_secret_candidate": True,
            "confidence": max(
                item["confidence"]
                for item in matches
            ),
            "matches": matches,
        }

    # ========================================================
    # MAIN ANALYZER
    # ========================================================

    @classmethod
    def analyze(
        cls,
        raw_assets: dict
    ) -> dict:

        result = {
            "URLs": [],
            "Domains": [],
            "Subdomains": [],
            "Apex Domains": [],
            "IPv4": [],
            "Emails": [],
            "Hashes": [],
            "JWT-like": [],
            "Paths": [],
            "Secret Candidates": [],
            "Security Keyword Lines": [],
        }

        # ----------------------------------------------------
        # URLs
        # ----------------------------------------------------

        for value in raw_assets.get(
            "URLs",
            []
        ):

            normalized = cls.normalize_url(
                value
            )

            if not normalized:

                result["URLs"].append(
                    {
                        "value": value,
                        "normalized": None,
                        "valid": False,
                        "confidence": 0.0,
                    }
                )

                continue

            parsed = urlsplit(
                normalized
            )

            result["URLs"].append(
                {
                    "value": value,
                    "normalized": normalized,
                    "host": parsed.hostname,
                    "scheme": parsed.scheme,
                    "path": parsed.path,
                    "query": parsed.query,
                    "valid": True,
                    "confidence": 0.99,
                }
            )

        # ----------------------------------------------------
        # DOMAINS
        # ----------------------------------------------------

        seen_domains = set()

        for value in raw_assets.get(
            "Domains",
            []
        ):

            normalized = cls.normalize_domain(
                value
            )

            if not normalized:
                continue

            if normalized in seen_domains:
                continue

            seen_domains.add(
                normalized
            )

            full_domain, apex = (
                cls.split_domain(
                    normalized
                )
            )

            is_subdomain = (
                full_domain != apex
            )

            result["Domains"].append(
                {
                    "value": value,
                    "normalized": full_domain,
                    "valid": True,
                    "type": (
                        "Subdomain"
                        if is_subdomain
                        else "Domain"
                    ),
                    "confidence": 0.98,
                }
            )

            if is_subdomain:

                result["Subdomains"].append(
                    {
                        "value": full_domain,
                        "apex_domain": apex,
                        "confidence": 0.98,
                    }
                )

            result["Apex Domains"].append(
                {
                    "value": apex,
                    "confidence": 0.98,
                }
            )

        # ----------------------------------------------------
        # IPv4
        # ----------------------------------------------------

        for value in raw_assets.get(
            "IPv4",
            []
        ):

            valid = cls.validate_ipv4(
                value
            )

            result["IPv4"].append(
                {
                    "value": value,
                    "valid": valid,
                    "confidence": (
                        0.99
                        if valid
                        else 0.0
                    ),
                }
            )

        # ----------------------------------------------------
        # EMAILS
        # ----------------------------------------------------

        for value in raw_assets.get(
            "Emails",
            []
        ):

            domain = (
                value.rsplit(
                    "@",
                    1
                )[1].lower()
                if "@" in value
                else None
            )

            result["Emails"].append(
                {
                    "value": value,
                    "domain": domain,
                    "valid": True,
                    "confidence": 0.99,
                }
            )

        # ----------------------------------------------------
        # HASHES
        # ----------------------------------------------------

        for value in raw_assets.get(
            "Hashes",
            []
        ):

            result["Hashes"].append(
                cls.analyze_hash(
                    value
                )
            )

        # ----------------------------------------------------
        # JWT
        # ----------------------------------------------------

        for value in raw_assets.get(
            "JWT-like",
            []
        ):

            result["JWT-like"].append(
                cls.analyze_jwt(
                    value
                )
            )

        # ----------------------------------------------------
        # PATHS
        # ----------------------------------------------------

        for value in raw_assets.get(
            "Paths",
            []
        ):

            valid = (
                isinstance(
                    value,
                    str
                )
                and value.startswith("/")
                and not value.startswith("//")
            )

            result["Paths"].append(
                {
                    "value": value,
                    "valid": valid,
                    "confidence": (
                        0.95
                        if valid
                        else 0.0
                    ),
                }
            )

        # ----------------------------------------------------
        # SECRETS
        # ----------------------------------------------------

        for value in raw_assets.get(
            "Security keyword lines",
            []
        ):

            analysis = (
                cls.analyze_secret(
                    value
                )
            )

            if analysis[
                "is_secret_candidate"
            ]:

                result[
                    "Secret Candidates"
                ].append(
                    analysis
                )

            result[
                "Security Keyword Lines"
            ].append(
                {
                    "value": value,
                    "secret_candidate":
                        analysis[
                            "is_secret_candidate"
                        ],
                    "confidence":
                        analysis[
                            "confidence"
                        ],
                }
            )

        # ----------------------------------------------------
        # FINAL DEDUPE
        # ----------------------------------------------------

        for key in result:

            result[key] = (
                cls._unique_objects(
                    result[key]
                )
            )

        return result

    # ========================================================
    # OBJECT DEDUPLICATION
    # ========================================================

    @staticmethod
    def _unique_objects(
        values
    ):

        seen = set()
        result = []

        for item in values:

            marker = json.dumps(
                item,
                sort_keys=True,
                ensure_ascii=False
            )

            if marker in seen:
                continue

            seen.add(marker)
            result.append(item)

        return result