import io
from fontTools.ttLib import TTFont
from ..misc.ftFont import FTFont
from ..misc.hbShape import HBShape
from .baseFont import BaseFont
from ..misc.compilerPool import compileTTXToBytes


class _OTFBaseFont(BaseFont):

    def _getOutlinePath(self, glyphName, colorLayers):
        outline = self.ftFont.getOutlinePath(glyphName)
        if colorLayers:
            return [(outline, 0)]
        else:
            return outline

    def varLocationChanged(self, varLocation):
        self.ftFont.setVarLocation(varLocation if varLocation else {})


class OTFFont(_OTFBaseFont):

    def __init__(self, fontPath, fontNumber):
        super().__init__(fontPath, fontNumber)
        with open(fontPath, "rb") as f:
            self.fontData = f.read()

    async def load(self, outputWriter):
        fontData = self.fontData
        f = io.BytesIO(fontData)
        self.ttFont = TTFont(f, fontNumber=self.fontNumber, lazy=True)
        if self.ttFont.flavor in ("woff", "woff2"):
            self.ttFont.flavor = None
            self.ttFont.recalcBBoxes = False
            self.ttFont.recalcTimestamp = False
            f = io.BytesIO()
            self.ttFont.save(f, reorderTables=False)
            fontData = f.getvalue()
        self.ftFont = FTFont(fontData, fontNumber=self.fontNumber, ttFont=self.ttFont)
        self.shaper = HBShape(fontData, fontNumber=self.fontNumber, ttFont=self.ttFont)


class TTXFont(_OTFBaseFont):

    def __init__(self, fontPath, fontNumber):
        super().__init__(fontPath, fontNumber)

    def updateFontPath(self, newFontPath):
        self.fontPath = newFontPath

    def canReloadWithChange(self, externalFilePath):
        # For TTX we might as well return False, but this was a nice test
        # case for resetCache(). More serious usage will follow in UFOFont.
        self.resetCache()
        return True

    async def load(self, outputWriter):
        fontData = await compileTTXToBytes(self.fontPath, outputWriter)
        f = io.BytesIO(fontData)
        self.ttFont = TTFont(f, fontNumber=self.fontNumber, lazy=True)
        self.ftFont = FTFont(fontData, fontNumber=self.fontNumber, ttFont=self.ttFont)
        self.shaper = HBShape(fontData, fontNumber=self.fontNumber, ttFont=self.ttFont)
