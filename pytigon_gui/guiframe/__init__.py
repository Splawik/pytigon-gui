"""
Hierarchia okien aplikacji:
  appframe.SChAppFrame
    self.Desktop = appframe.SchNotebook
      appframe.SchNotebook
        appnotebookpage.SchNotebookPage
            SChSashWindow (spełnia funkcję ParmObj)
              self.header = SChFrame
              self.body = SChFrame
              self.footer = SChFrame
              self.panel = SChFrame
"""
