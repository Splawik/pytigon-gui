"""Server data proxy for grid tables.

Provides DataProxy: a communication layer that fetches paginated
data from a Django backend via HTTP, supporting CRUD operations,
sorting, autocomplete, and column metadata retrieval.
"""

import logging

import wx

from pytigon_lib.schtools import schjson

logger = logging.getLogger(__name__)

_ = wx.GetTranslation


CMD_INFO = 1
CMD_PAGE = 2
CMD_COUNT = 3
CMD_SYNC = 4
CMD_AUTO = 5
CMD_RECASSTR = 6
CMD_EXEC = 7


class NullProxy:
    """Stand-in proxy used when the data source cannot be reached.

    Implements just enough of the :class:`DataProxy` interface for a grid to
    be built and displayed with zero rows, so a failed HTTP request degrades
    to an empty grid instead of raising out of the HTML parser.
    """

    is_valid = False

    def __init__(self, address=""):
        """Initialize the empty proxy.

        Args:
            address: The unreachable table address, kept for diagnostics.
        """
        self.tabaddress = address
        self.parm = dict()

    def set_parent(self, parent):
        """Accept (and ignore) the owning table."""

    def set_address(self, address):
        """Accept (and ignore) a new address."""

    def get_address(self):
        """Return the unreachable table address."""
        return self.tabaddress

    def set_address_parm(self, parm):
        """Accept (and ignore) address parameters."""
        self.parm = parm

    def get_address_parm(self):
        """Return the address parameters."""
        return self.parm

    def set_parm(self, key, value):
        """Store a query parameter."""
        self.parm[key] = value

    def get_max_count(self):
        """Return an empty record count."""
        return 0

    def get_count(self):
        """Return an empty record count."""
        return 0

    def get_page(self, nrPage):
        """Return no records for the requested page."""
        return []

    def get_default_rec(self):
        """Return a single empty cell as the default record."""
        return [""]

    def sync_data(self, listaRecUpdate, listaRecInsert, listaRecDelete):
        """Discard pending changes - there is nothing to sync."""

    def auto_update(self, col_name, col_names, rec):
        """Return the record unchanged."""
        return rec

    def clone(self):
        """Return another empty proxy for the same address."""
        return NullProxy(self.tabaddress)

    def run(self, parm):
        """Reject server commands: return None."""
        return None

    def GetRecAsStr(self, nrRec):
        """Return an empty record representation."""
        return ""

    def GetColNames(self):
        """Return a single placeholder column name."""
        return [""]

    def GetAutoCols(self):
        """Return no auto-refresh columns."""
        return []

    def GetColTypes(self):
        """Return a single 'string' column type."""
        return ["string"]

    def GetColSize(self):
        """Return a single default column width."""
        return [32]

    def GetColIcons(self):
        """Return no column icons."""
        return None


def process_post_parm(obj):
    ret = {}
    for key, value in list(obj.items()):
        ret[key] = schjson.dumps(value)
    return ret


class DataProxy:
    def __init__(self, http, tabaddress):
        self.max_count = 1000000
        self.var_count = -1
        self.tabaddress = tabaddress
        self.tabaddress0 = self.tabaddress
        self.parm = ""
        self.parent = None
        self.http = http
        self.col_types2 = []
        self.parm = dict()
        self.is_valid = True

        response = self.http.post(
            self.parent,
            self.tabaddress,
            process_post_parm(
                {
                    "cmd": CMD_INFO,
                }
            ),
        )
        if response is None:
            self.is_valid = False
            raise RuntimeError(f"Failed to get table info from {self.tabaddress}")
        ret = schjson.loads(response.str())
        self.col_names = ret["col_names"]
        self.col_types = ret["col_types"]
        self.default_rec = ret["default_rec"]
        self.col_size = ret["col_length"]

        for i in range(0, len(self.col_size)):
            if self.col_size[i] > 32:
                self.col_size[i] = 32

        self.auto_cols = ret["auto_cols"]

        for col in self.col_types:
            self.col_types2.append(col.split(":")[0])

        self.tab_conw = {
            "long": self.conw_long,
            "string": self.conw_none,
            "double": self.conw_float,
            "bool": self.conw_bool,
            "choice": self.conw_none,
            "x": self.conw_none,
        }

    def set_parent(self, parent):
        self.parent = parent

    def set_address(self, address):
        self.tabaddress = self.tabaddress0 + address

    def get_address(self):
        return self.tabaddress

    def set_address_parm(self, parm):
        if self.parm == parm:
            return False
        else:
            self.parm = parm
            return True

    def get_address_parm(self):
        return self.parm

    def conw_long(self, l):
        if l:
            return int(l)
        else:
            return None

    def conw_none(self, n):
        if n is not None:
            return n
        else:
            return ""

    def conw_float(self, f):
        if f:
            return float(f)
        else:
            return None

    def conw_bool(self, b):
        if b:
            return bool(b)
        else:
            return None

    def _reformat_rec(self, rec):
        ret = []
        for i, col in enumerate(rec):
            convert = self.tab_conw.get(self.col_types2[i], self.conw_none)
            ret.append(convert(col))
        return ret

    def set_parm(self, key, value):
        (self.parm)[key] = value

    def get_page(self, nrPage):
        c = {"cmd": CMD_PAGE, "nr": nrPage}
        if self.parm:
            for key, value in list(self.parm.items()):
                c[key] = value
        response = self.http.post(self.parent, self.tabaddress, process_post_parm(c))

        try:
            page = schjson.loads(response.str())
            retpage = page["page"]
        except (KeyError, ValueError, TypeError):
            logger.exception("Failed to decode grid page from %s", self.tabaddress)
            retpage = []
            self.http.show(wx.GetApp().GetTopWindow())
        return retpage

    def get_max_count(self):
        return self.max_count

    def get_count(self):
        parm = {"cmd": CMD_COUNT}
        if "value" in self.parm:
            parm["value"] = self.parm["value"]
        response = self.http.post(self.parent, self.tabaddress, process_post_parm(parm))
        s = response.str()
        ret = schjson.loads(s)
        self.max_count = int(ret["count"])
        return self.max_count

    def sync_data(self, listaRecUpdate, listaRecInsert, listaRecDelete):
        update = schjson.dumps(listaRecUpdate)
        insert = schjson.dumps(listaRecInsert)
        delete = schjson.dumps(listaRecDelete)
        c = {"cmd": CMD_SYNC, "update": update, "insert": insert, "delete": delete}
        self.http.post(self.parent, self.tabaddress, process_post_parm(c))

    def auto_update(self, col_name, col_names, rec):
        """Return transformed row after current row is changed"""

        col_name2 = schjson.dumps(col_name)
        col_names2 = schjson.dumps(col_names)
        rec2 = schjson.dumps(rec)

        c = {
            "cmd": CMD_AUTO,
            "col_name": col_name2,
            "col_names": col_names2,
            "rec": rec2,
        }

        response = self.http.post(self.parent, self.tabaddress, process_post_parm(c))
        ret = schjson.loads(response.str())
        if ret is None:
            return rec
        else:
            return ret["rec"]

    def clone(self):
        c = DataProxy(self.http, self.tabaddress)
        c.set_address_parm(self.get_address_parm())
        return c

    def run(self, parm):
        """Execute a server-side command and return its decoded result.

        Args:
            parm: Opaque command payload forwarded to the backend.

        Returns:
            The decoded server response.
        """
        c = {"cmd": CMD_EXEC, "value": parm}
        response = self.http.post(self.parent, self.tabaddress, process_post_parm(c))
        ret = schjson.loads(response.str())
        return ret

    def get_default_rec(self):
        return self.default_rec

    def GetRecAsStr(self, nrRec):
        response = self.http.post(
            self.parent,
            self.tabaddress,
            process_post_parm({"cmd": CMD_RECASSTR, "nr": nrRec}),
        )
        ret = schjson.loads(response.str())
        return ret["recasstr"]

    def GetColNames(self):
        return self.col_names

    def GetAutoCols(self):
        return self.auto_cols

    def GetColTypes(self):
        return self.col_types

    def GetColSize(self):
        return self.col_size

    def GetColIcons(self):
        return None
