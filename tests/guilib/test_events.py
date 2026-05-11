"""Tests for pytigon_gui.guilib.events - event ID registration."""

import pytest


class TestEventIds:
    """Verify all wx event IDs are created and unique."""

    def test_all_ids_are_integers(self):
        """All event IDs should be integers (from wx.NewId())."""
        from pytigon_gui.guilib import events

        id_names = [
            attr
            for attr in dir(events)
            if attr.startswith("ID_") and not attr.startswith("__")
        ]

        for name in id_names:
            val = getattr(events, name)
            assert isinstance(val, int), f"{name} should be int, got {type(val)}"

    def test_all_ids_unique(self):
        """All event IDs should be unique."""
        from pytigon_gui.guilib import events

        id_names = [
            attr
            for attr in dir(events)
            if attr.startswith("ID_") and not attr.startswith("__")
        ]

        values = [getattr(events, name) for name in id_names]
        assert len(values) == len(set(values)), "Duplicate event IDs found: " + str(
            [v for v in values if values.count(v) > 1]
        )

    def test_expected_ids_exist(self):
        """Verify canonical event IDs are present."""
        from pytigon_gui.guilib import events

        expected = [
            "ID_START",
            "ID_NEXTTAB",
            "ID_PREVTAB",
            "ID_CLOSETAB",
            "ID_EXIT",
            "ID_UNDO",
            "ID_REDO",
            "ID_CUT",
            "ID_COPY",
            "ID_PASTE",
            "ID_HELP",
            "ID_ZOOM",
            "ID_PRINT",
            "ID_PRINT_PREVIEW",
            "ID_FIND",
            "ID_REPLACE",
            "ID_LOAD",
            "ID_SAVE",
            "ID_SAVE_AS",
            "ID_END",
        ]

        for name in expected:
            assert hasattr(events, name), f"Missing event ID: {name}"

    def test_id_count(self):
        """Verify the expected number of event IDs (45 based on source)."""
        from pytigon_gui.guilib import events

        id_names = [
            attr
            for attr in dir(events)
            if attr.startswith("ID_") and not attr.startswith("__")
        ]
        # At least 45 event IDs defined in the source
        # (wx module also exports its own ID_* constants via 'import wx')
        assert len(id_names) >= 45

    def test_no_extra_non_id_attributes(self):
        """Ensure module only exports ID_* constants and wx."""
        import pytigon_gui.guilib.events as events_module

        public = [attr for attr in dir(events_module) if not attr.startswith("_")]
        for attr in public:
            assert attr.startswith("ID_") or attr == "wx", (
                f"Unexpected public attribute: {attr}"
            )
