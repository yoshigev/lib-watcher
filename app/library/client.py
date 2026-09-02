import re
import json
import logging
import urllib.request
import urllib.parse
import ssl
from typing import Dict, List, Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)

_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE

class LibraryCatalogClient:
    def __init__(self):
        self.session_cookie = ""

    @property
    def search_tree_url(self) -> str:
        return f"{settings.LIBRARY_BASE_URL}/BuildaGate8library/general2/company_search_tree.php"

    @property
    def book_detail_url(self) -> str:
        return f"{settings.LIBRARY_BASE_URL}/BuildaGate8library/general2/product_card_edit.php"

    @property
    def headers(self) -> Dict[str, str]:
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Referer': f"{self.search_tree_url}?mc={settings.LIBRARY_NEW_NAME_MADE}~Card1",
        }
    
    def get_session(self) -> str:
        """Retrieve fresh PHPSESSID cookie from catalog homepage."""
        try:
            req = urllib.request.Request(
                f"{self.search_tree_url}?mc={settings.LIBRARY_NEW_NAME_MADE}~Card1",
                headers=self.headers
            )
            with urllib.request.urlopen(req, context=_ssl_context, timeout=12) as resp:
                cookie = resp.headers.get('Set-Cookie', '')
                for part in cookie.split(';'):
                    if 'PHPSESSID' in part:
                        self.session_cookie = part.strip()
                        break
        except Exception as e:
            logger.error(f"Error fetching session: {e}")
        return self.session_cookie

    def _strip_html(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"')
        text = text.replace('&#039;', "'").replace('&lt;', '<').replace('&gt;', '>')
        return re.sub(r'\s+', ' ', text).strip()

    def search(self, query: str, field: str = "General", card_type: str = "Card1", page: int = 1) -> Dict[str, Any]:
        if not self.session_cookie:
            self.get_session()

        post_data = {
            'NewNameMade': settings.LIBRARY_NEW_NAME_MADE,
            'Referral': 'button',
            'FromRec': '',
            'SiteName': settings.LIBRARY_SITE_NAME,
            'CNumber': '',
            'SearchType': card_type,
            'BuyerID': settings.LIBRARY_BUYER_ID,
            'Clubtmp1': '',
            'comefrom': '',
            'DataCardTemplate': '',
            'framemode': '',
            'framesource': '',
            'CardPrice': '',
            'BANNER': '',
            'goToSearchWithItm': '',
            'goToSearchWithCrd': '',
            'chosenItem': '',
            'cndLikeOrEq': '',
            'lgFlag': '',
            'FreeText_1': query,
            'SearchFildType_1': field,
            'ThisCard': card_type,
            'FocusCard': card_type,
            'SearchAll': '',
            'z1': '20',
        }

        req_headers = dict(self.headers)
        req_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        if self.session_cookie:
            req_headers['Cookie'] = self.session_cookie

        body = urllib.parse.urlencode(post_data).encode('utf-8')
        try:
            req = urllib.request.Request(self.search_tree_url, data=body, headers=req_headers, method='POST')
            with urllib.request.urlopen(req, context=_ssl_context, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                return self._parse_search_results(html)
        except Exception as e:
            logger.error(f"Error during search for '{query}': {e}")
            return {'total': 0, 'page_current': 1, 'page_total': 1, 'books': [], 'error': str(e)}

    def _parse_search_results(self, html: str) -> Dict[str, Any]:
        books = []
        
        total_m = re.search(r'נמצאו\s+(\d+)', html)
        total = int(total_m.group(1)) if total_m else 0

        page_m = re.search(r'עמוד\s+(\d+)\s+מתוך\s+(\d+)', html)
        page_current = int(page_m.group(1)) if page_m else 1
        page_total = int(page_m.group(2)) if page_m else 1

        chunks = re.split(r'name=["\']choose_(\d+)["\']', html)
        seen_ids = set()

        for i in range(1, len(chunks), 2):
            item_id = chunks[i]
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)
            content = chunks[i+1]

            card_m = re.search(r"date_card_popup\('" + item_id + r"',\s*'([^']+)'\)", content)
            card_type = card_m.group(1) if card_m else "Card1"

            title = ""
            title_m = re.search(r'aria-label="שם הכותר[^"]*"[^>]*><span[^>]*>(.*?)</span></a>', content, re.DOTALL)
            if title_m:
                title = self._strip_html(title_m.group(1))
            else:
                title_m2 = re.search(r"date_card_popup\('" + item_id + r"',[^)]*\)[^>]*><span[^>]*>(.*?)</span></a>", content, re.DOTALL)
                if title_m2:
                    title = self._strip_html(title_m2.group(1))

            series_spans = re.findall(r'class="spnSrsClss"[^>]*>(.*?)</span>', content, re.DOTALL)
            series_parts = [self._strip_html(s) for s in series_spans if self._strip_html(s)]
            series_text = " • ".join(series_parts) if series_parts else ""

            author = ""
            author_m = re.search(r'aria-label="שם המחבר/ת[^"]*"[^>]*>(?:<[^>]+>)*(.*?)(?:</a>|</td>)', content, re.DOTALL)
            if author_m:
                author = self._strip_html(author_m.group(1))

            copies_avail = 0
            is_available = False
            
            msg_m = re.search(r"printAbsMsg\('([^']+)'", content)
            if msg_m:
                raw_msg = self._strip_html(msg_m.group(1))
                num_m = re.search(r'קיימים\s+(\d+)\s+עותקים', raw_msg)
                if num_m:
                    copies_avail = int(num_m.group(1))
                    is_available = (copies_avail > 0)
                elif 'לא קיימים' in raw_msg or 'לא קיים' in raw_msg:
                    copies_avail = 0
                    is_available = False
                elif 'קיים עותק' in raw_msg or 'קיימים' in raw_msg:
                    copies_avail = 1
                    is_available = True
            
            if 'border:2px solid green' in content:
                is_available = True
                if copies_avail == 0:
                    copies_avail = 1
            elif 'border:2px solid red' in content:
                is_available = False
                copies_avail = 0

            books.append({
                'item_id': item_id,
                'card_type': card_type,
                'title': title,
                'series': series_text,
                'author': author,
                'is_available': is_available,
                'copies_available': copies_avail,
                'detail_url': f"{self.book_detail_url}?SiteName={settings.LIBRARY_SITE_NAME}&Clubtmp1=&CNumber=&NewNameMade={settings.LIBRARY_NEW_NAME_MADE}&ItemID={item_id}&Card={card_type}&Daf=1"
            })

        return {
            'total': total,
            'page_current': page_current,
            'page_total': page_total,
            'books': books
        }

    def get_book_availability(self, item_id: str, card_type: str = "Card1") -> Dict[str, Any]:
        url = f"{self.book_detail_url}?SiteName={settings.LIBRARY_SITE_NAME}&Clubtmp1=&CNumber=&NewNameMade={settings.LIBRARY_NEW_NAME_MADE}&ItemID={item_id}&Card={card_type}&Daf=1"
        req_headers = dict(self.headers)
        if self.session_cookie:
            req_headers['Cookie'] = self.session_cookie

        try:
            req = urllib.request.Request(url, headers=req_headers)
            with urllib.request.urlopen(req, context=_ssl_context, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                return self._parse_book_copies(html, item_id, card_type)
        except Exception as e:
            logger.error(f"Error fetching availability for item {item_id}: {e}")
            return {
                'item_id': item_id,
                'card_type': card_type,
                'title': '',
                'author': '',
                'is_available': False,
                'copies_available': 0,
                'copies_total': 0,
                'copies_list': [],
                'error': str(e)
            }

    def _parse_book_copies(self, html: str, item_id: str, card_type: str) -> Dict[str, Any]:
        title = ""
        title_m = re.search(r'<b>כותר:</b>\s*([^<]+)', html)
        if title_m:
            title = self._strip_html(title_m.group(1))

        author = ""
        author_m = re.search(r'<b>שם המחבר:</b>\s*([^<]+)', html)
        if author_m:
            author = self._strip_html(author_m.group(1))

        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
        copies_list = []
        available_count = 0
        total_count = 0

        for r in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL | re.IGNORECASE)
            cleaned = [self._strip_html(c) for c in cells]
            cleaned = [c for c in cleaned if c]
            
            if len(cleaned) >= 3:
                status_cell = ""
                for cell in cleaned:
                    if cell in ('פנוי', 'מושאל', 'זמין', 'לא להשאלה', 'שמור'):
                        status_cell = cell
                
                if status_cell:
                    barcode = cleaned[0] if len(cleaned) > 0 else ""
                    branch = cleaned[1] if len(cleaned) > 1 else ""
                    section = cleaned[2] if len(cleaned) > 2 else ""

                    is_free = (status_cell == 'פנוי' or status_cell == 'זמין')
                    if is_free:
                        available_count += 1
                    total_count += 1

                    copies_list.append({
                        'barcode': barcode,
                        'branch': branch,
                        'section': section,
                        'status': status_cell,
                        'is_available': is_free
                    })

        return {
            'item_id': item_id,
            'card_type': card_type,
            'title': title,
            'author': author,
            'is_available': (available_count > 0),
            'copies_available': available_count,
            'copies_total': total_count,
            'copies_list': copies_list
        }

catalog_client = LibraryCatalogClient()
