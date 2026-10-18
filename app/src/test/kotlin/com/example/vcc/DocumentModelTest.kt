package com.example.vcc.document

import org.junit.Test
import org.junit.Assert.*

class DocumentModelTest {

    @Test
    fun testB5PaperDimensions() {
        val b5 = PaperSize.B5
        assertEquals(176.0, b5.widthMm, 0.001)
        assertEquals(250.0, b5.heightMm, 0.001)
        assertEquals("B5", b5.name)
    }

    @Test
    fun testDefaultPageConfig() {
        val config = PageConfig()
        assertEquals(PaperSize.B5, config.paperSize)
        assertEquals(20.0, config.leftMarginMm, 0.001)
        assertEquals(20.0, config.topMarginMm, 0.001)
        assertEquals(20.0, config.rightMarginMm, 0.001)
        assertEquals(20.0, config.bottomMarginMm, 0.001)
        assertEquals(8.0, config.lineSpacingMm, 0.001)
    }

    @Test
    fun testContentRect() {
        val config = PageConfig(
            paperSize = PaperSize.B5,
            leftMarginMm = 20.0,
            topMarginMm = 20.0,
            rightMarginMm = 20.0,
            bottomMarginMm = 20.0
        )
        val content = config.contentRectMm()
        assertEquals(20.0, content.left, 0.001)
        assertEquals(20.0, content.top, 0.001)
        assertEquals(156.0, content.right, 0.001)  // 176 - 20
        assertEquals(230.0, content.bottom, 0.001)  // 250 - 20
        assertEquals(136.0, content.width, 0.001)   // 156 - 20
        assertEquals(210.0, content.height, 0.001)  // 230 - 20
    }

    @Test
    fun testComputeLineCount() {
        val config = PageConfig(
            paperSize = PaperSize.B5,
            topMarginMm = 20.0,
            bottomMarginMm = 20.0,
            lineSpacingMm = 8.0
        )
        val lineCount = config.computeLineCount()
        // Content height = 250 - 20 - 20 = 210mm
        // Lines = 210 / 8 = 26.25 -> 26
        assertEquals(26, lineCount)
    }

    @Test
    fun testComputeLineCountWithExplicit() {
        val config = PageConfig(
            paperSize = PaperSize.B5,
            lineCount = 10
        )
        assertEquals(10, config.computeLineCount())
    }

    @Test
    fun testMmToPx() {
        val config = PageConfig()
        val px = config.mmToPx(25.4, 96.0)
        assertEquals(96.0, px, 0.001)
    }

    @Test
    fun testPxToMm() {
        val config = PageConfig()
        val mm = config.pxToMm(96.0, 96.0)
        assertEquals(25.4, mm, 0.001)
    }

    @Test
    fun testValidateValidConfig() {
        val config = PageConfig()
        val result = config.validate()
        assertTrue("Valid config should pass validation", result.isValid)
        assertTrue("No errors expected", result.errors.isEmpty())
    }

    @Test
    fun testValidateNegativeMargins() {
        val config = PageConfig(leftMarginMm = -5.0)
        val result = config.validate()
        assertFalse("Negative margins should fail validation", result.isValid)
        assertFalse("Should have errors", result.errors.isEmpty())
    }

    @Test
    fun testValidateExcessiveMargins() {
        val config = PageConfig(
            paperSize = PaperSize.B5,
            leftMarginMm = 100.0,
            rightMarginMm = 100.0
        )
        val result = config.validate()
        assertFalse("Excessive margins should fail validation", result.isValid)
    }

    @Test
    fun testValidateInvalidLineSpacing() {
        val config = PageConfig(lineSpacingMm = 0.0)
        val result = config.validate()
        assertFalse("Zero line spacing should fail validation", result.isValid)
    }

    @Test
    fun testValidateInvalidWatermarkAlpha() {
        val config = PageConfig(watermarkAlpha = 2.0f)
        val result = config.validate()
        assertFalse("Watermark alpha > 1 should fail validation", result.isValid)
    }

    @Test
    fun testContentRectContains() {
        val rect = ContentRect(10.0, 10.0, 100.0, 100.0)
        assertTrue(rect.contains(50.0, 50.0))
        assertTrue(rect.contains(10.0, 10.0))
        assertTrue(rect.contains(100.0, 100.0))
        assertFalse(rect.contains(5.0, 50.0))
        assertFalse(rect.contains(105.0, 50.0))
    }

    @Test
    fun testNotebookDocumentEmpty() {
        val doc = NotebookDocument.empty("Test")
        assertEquals("Test", doc.title)
        assertEquals(PaperSize.B5, doc.paperSize)
        assertEquals(1, doc.pageCount)
        assertEquals(0, doc.pages[0].index)
    }

    @Test
    fun testNotebookDocumentAddPage() {
        val doc = NotebookDocument.empty("Test")
        val newDoc = doc.addPage()
        assertEquals(2, newDoc.pageCount)
        assertEquals(1, newDoc.pages[1].index)
    }

    @Test
    fun testNotebookDocumentWithPage() {
        val doc = NotebookDocument.empty("Test")
        val newDoc = doc.withPage(0, "Hello, world!", true)
        assertEquals("Hello, world!", newDoc.pages[0].content)
        assertTrue(newDoc.pages[0].hasHandwriting)
    }

    @Test
    fun testNotebookDocumentGetPage() {
        val doc = NotebookDocument.empty("Test")
        assertNotNull(doc.getPage(0))
        assertNull(doc.getPage(1))
        assertNull(doc.getPage(-1))
    }

    @Test
    fun testPaperSizeFromName() {
        assertEquals(PaperSize.A4, PaperSize.fromName("A4"))
        assertEquals(PaperSize.B5, PaperSize.fromName("B5"))
        assertEquals(PaperSize.B5, PaperSize.fromName("UNKNOWN"))
    }
}