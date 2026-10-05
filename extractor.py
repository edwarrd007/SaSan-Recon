import ipaddress
import re


class Extractor:

    # ========================================================
    # REGEX
    # ========================================================

    URL_RE = re.compile(
        r"""https?://[^\s<>"']+""",
        re.I
    )

    EMAIL_RE = re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.I
    )

    IPV4_RE = re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    )

    DOMAIN_RE = re.compile(
        r"\b(?:"
        r"[A-Z0-9]"
        r"(?:[A-Z0-9-]{0,61}[A-Z0-9])?"
        r"\."
        r")+"
        r"[A-Z]{2,}\b",
        re.I
    )

    HASH_RE = re.compile(
        r"\b(?:"
        r"[a-f0-9]{32}|"
        r"[a-f0-9]{40}|"
        r"[a-f0-9]{64}|"
        r"[a-f0-9]{96}|"
        r"[a-f0-9]{128}"
        r")\b",
        re.I
    )

    JWT_RE = re.compile(
        r"\b"
        r"[A-Za-z0-9_-]+\."
        r"[A-Za-z0-9_-]+\."
        r"[A-Za-z0-9_-]+"
        r"\b"
    )

    SECRET_RE = re.compile(
        r"(?im)^.*\b(?:"
        r"api[_-]?key|"
        r"access[_-]?token|"
        r"secret|"
        r"authorization|"
        r"password|"
        r"passwd|"
        r"client_secret"
        r")\b.*$"
    )

    PATH_RE = re.compile(
        r"(?<![A-Za-z0-9])/"
        r"(?:"
        r"[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+"
        r")"
    )

    # ========================================================
    # UNIQUE
    # ========================================================

    @staticmethod
    def _uniq(values):

        return list(
            dict.fromkeys(values)
        )

    # ========================================================
    # EXTRACT
    # ========================================================

    @classmethod
    def extract(
        cls,
        text: str
    ) -> dict[str, list[str]]:

        if not isinstance(
            text,
            str
        ):
            text = ""

        if not text:
            return {
                "URLs": [],
                "Domains": [],
                "IPv4": [],
                "Emails": [],
                "Hashes": [],
                "JWT-like": [],
                "Paths": [],
                "Security keyword lines": [],
            }

        # ----------------------------------------------------
        # URLs
        # ----------------------------------------------------

        urls = cls._uniq(
            x.rstrip(".,);]}")
            for x in cls.URL_RE.findall(text)
        )

        # ----------------------------------------------------
        # Emails
        # ----------------------------------------------------

        emails = cls._uniq(
            cls.EMAIL_RE.findall(text)
        )

        # ----------------------------------------------------
        # IPv4
        # ----------------------------------------------------

        ips = []

        for value in cls._uniq(
            cls.IPV4_RE.findall(text)
        ):

            try:

                ip = ipaddress.ip_address(
                    value
                )

                if isinstance(
                    ip,
                    ipaddress.IPv4Address
                ):
                    ips.append(value)

            except ValueError:
                continue

        # ----------------------------------------------------
        # Domains
        # ----------------------------------------------------

        domains = cls._uniq(
            cls.DOMAIN_RE.findall(text)
        )

        # ----------------------------------------------------
        # Hashes
        # ----------------------------------------------------

        hashes = cls._uniq(
            cls.HASH_RE.findall(text)
        )

        # ----------------------------------------------------
        # JWT-like
        # ----------------------------------------------------

        jwts = cls._uniq(
            cls.JWT_RE.findall(text)
        )

        # ----------------------------------------------------
        # Security keyword lines
        # ----------------------------------------------------

        secrets = cls._uniq(
            line.strip()
            for line in cls.SECRET_RE.findall(text)
        )

        # ----------------------------------------------------
        # Paths
        # ----------------------------------------------------

        paths = cls._uniq(
            cls.PATH_RE.findall(text)
        )

        return {
            "URLs": urls,
            "Domains": domains,
            "IPv4": ips,
            "Emails": emails,
            "Hashes": hashes,
            "JWT-like": jwts,
            "Paths": paths,
            "Security keyword lines": secrets,
        }