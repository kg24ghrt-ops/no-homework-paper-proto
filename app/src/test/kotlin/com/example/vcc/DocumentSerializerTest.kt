package com.example.vcc.document

import org.junit.Test
import org.junit.Assert.*

class DocumentSerializerTest {

    @Test
    fun testSerializeAndDeserialize() {
        val doc = NotebookDocument.empty("Test Document")
        val data = DocumentSerializer.serialize(doc)
        assertTrue("Serialized data should not be empty", data.isNotEmpty())

        val restored = DocumentSerializer.deserialize(data)
        assertEquals("Test Document", restored.title)
        assertEquals(PaperSize.B5, restored.paperSize)
        assertEquals(1, restored.pageCount)
    }

    @Test
    fun testSerializeWithMultiplePages() {
        val doc = NotebookDocument.empty("Multi-page")
        val multiPage = doc.addPage().addPage()
        assertEquals(3, multiPage.pageCount)

        val data = DocumentSerializer.serialize(multiPage)
        val restored = DocumentSerializer.deserialize(data)
        assertEquals(3, restored.pageCount)
    }

    @Test
    fun testSerializeWithContent() {
        val doc = NotebookDocument.empty("Content Test")
        val withContent = doc.withPage(0, "Hello Myanmar မြန်မာ", true)
        val data = DocumentSerializer.serialize(withContent)
        val restored = DocumentSerializer.deserialize(data)
        assertEquals("Hello Myanmar မြန်မာ", restored.pages[0].content)
        assertTrue(restored.pages[0].hasHandwriting)
    }

    @Test
    fun testSerializeWithCustomConfig() {
        val config = PageConfig(
            paperSize = PaperSize.A4,
            leftMarginMm = 25.0,
            topMarginMm = 25.0,
            lineSpacingMm = 10.0
        )
        val doc = NotebookDocument(title = "Custom", paperSize = PaperSize.A4, pageConfig = config)
        val data = DocumentSerializer.serialize(doc)
        val restored = DocumentSerializer.deserialize(data)
        assertEquals(PaperSize.A4, restored.paperSize)
        assertEquals(25.0, restored.pageConfig.leftMarginMm, 0.001)
        assertEquals(10.0, restored.pageConfig.lineSpacingMm, 0.001)
    }

    @Test
    fun testInvalidMagicHeader() {
        val invalidData = byteArrayOf(0x00, 0x00, 0x00, 0x00)
        try {
            DocumentSerializer.deserialize(invalidData)
            fail("Should have thrown DocumentException")
        } catch (e: DocumentException) {
            assertTrue("Should mention invalid magic", e.message!!.contains("magic"))
        }
    }

    @Test
    fun testTruncatedData() {
        val validData = DocumentSerializer.serialize(NotebookDocument.empty("Test"))
        val truncated = validData.copyOfRange(0, validData.size / 2)
        try {
            DocumentSerializer.deserialize(truncated)
            fail("Should have thrown DocumentException for truncated data")
        } catch (e: DocumentException) {
            // Expected - either magic mismatch or EOF
            assertTrue("Should be a document exception", e is DocumentException)
        }
    }

    @Test
    fun testVeryShortData() {
        val shortData = byteArrayOf(0x41, 0x42)
        try {
            DocumentSerializer.deserialize(shortData)
            fail("Should have thrown DocumentException")
        } catch (e: DocumentException) {
            assertTrue("Should mention too short", e.message!!.contains("short", ignoreCase = true))
        }
    }

    @Test
    fun testIsValidDocument() {
        val validData = DocumentSerializer.serialize(NotebookDocument.empty("Test"))
        assertTrue(DocumentSerializer.isValidDocument(validData))

        val invalidData = byteArrayOf(0x00, 0x00, 0x00, 0x00)
        assertFalse(DocumentSerializer.isValidDocument(invalidData))

        val tooShort = byteArrayOf(0x56, 0x43)
        assertFalse(DocumentSerializer.isValidDocument(tooShort))
    }

    @Test
    fun testRoundTripPreservesAllFields() {
        val config = PageConfig(
            paperSize = PaperSize.A5,
            leftMarginMm = 15.0,
            topMarginMm = 18.0,
            rightMarginMm = 16.0,
            bottomMarginMm = 19.0,
            lineSpacingMm = 7.5,
            lineCount = 20,
            lineWidthPx = 1.5f,
            watermarkAlpha = 0.15f,
            showRuledLines = false,
            showWatermark = false
        )
        val doc = NotebookDocument(
            title = "Round Trip Test",
            paperSize = PaperSize.A5,
            pageConfig = config,
            pages = listOf(
                NotebookPage(0, config, "Page 1", true),
                NotebookPage(1, config, "Page 2", false)
            )
        )

        val data = DocumentSerializer.serialize(doc)
        val restored = DocumentSerializer.deserialize(data)

        assertEquals("Round Trip Test", restored.title)
        assertEquals(PaperSize.A5, restored.paperSize)
        assertEquals(15.0, restored.pageConfig.leftMarginMm, 0.001)
        assertEquals(18.0, restored.pageConfig.topMarginMm, 0.001)
        assertEquals(16.0, restored.pageConfig.rightMarginMm, 0.001)
        assertEquals(19.0, restored.pageConfig.bottomMarginMm, 0.001)
        assertEquals(7.5, restored.pageConfig.lineSpacingMm, 0.001)
        assertEquals(20, restored.pageConfig.lineCount)
        assertEquals(1.5f, restored.pageConfig.lineWidthPx, 0.001f)
        assertEquals(0.15f, restored.pageConfig.watermarkAlpha, 0.001f)
        assertEquals(false, restored.pageConfig.showRuledLines)
        assertEquals(false, restored.pageConfig.showWatermark)
        assertEquals(2, restored.pageCount)
        assertEquals("Page 1", restored.pages[0].content)
        assertTrue(restored.pages[0].hasHandwriting)
        assertEquals("Page 2", restored.pages[1].content)
        assertFalse(restored.pages[1].hasHandwriting)
    }
}