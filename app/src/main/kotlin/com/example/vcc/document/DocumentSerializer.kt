package com.example.vcc.document

import android.util.Log
import java.io.*
import java.util.zip.GZIPInputStream
import java.util.zip.GZIPOutputStream

/**
 * Handles serialization and deserialization of notebook documents.
 *
 * Format: A simple binary format with a header, JSON metadata, and compressed content.
 * This is designed to be forward-compatible and resilient to partial reads.
 */
class DocumentSerializer {

    companion object {
        private const val TAG = "DocumentSerializer"
        private const val FORMAT_VERSION = 1
        private const val MAGIC = "VCCN"  // Vcc Notebook
        private const val HEADER_SIZE = 4 + 4 + 4  // magic + version + data length

        /**
         * Serializes a notebook document to a byte array.
         */
        fun serialize(document: NotebookDocument): ByteArray {
            val ByteArrayOutputStream().use { baos ->
                DataOutputStream(GZIPOutputStream(baos)).use { dos ->
                    dos.writeUTF(document.title)
                    dos.writeDouble(document.paperSize.widthMm)
                    dos.writeDouble(document.paperSize.heightMm)
                    dos.writeUTF(document.paperSize.name)
                    dos.writeDouble(document.pageConfig.leftMarginMm)
                    dos.writeDouble(document.pageConfig.topMarginMm)
                    dos.writeDouble(document.pageConfig.rightMarginMm)
                    dos.writeDouble(document.pageConfig.bottomMarginMm)
                    dos.writeDouble(document.pageConfig.lineSpacingMm)
                    dos.writeInt(document.pageConfig.lineCount)
                    dos.writeFloat(document.pageConfig.lineWidthPx)
                    dos.writeFloat(document.pageConfig.watermarkAlpha)
                    dos.writeBoolean(document.pageConfig.showRuledLines)
                    dos.writeBoolean(document.pageConfig.showWatermark)
                    dos.writeInt(document.pages.size)

                    for (page in document.pages) {
                        dos.writeInt(page.index)
                        dos.writeUTF(page.content)
                        dos.writeBoolean(page.hasHandwriting)
                    }
                }
                return baos.toByteArray()
            }
        }

        /**
         * Deserializes a notebook document from a byte array.
         * @throws DocumentException if the data is malformed or truncated.
         */
        @Throws(DocumentException::class)
        fun deserialize(data: ByteArray): NotebookDocument {
            if (data.size < 4) {
                throw DocumentException("Data too short to contain magic header")
            }

            val magic = String(data.copyOfRange(0, 4))
            if (magic != MAGIC) {
                throw DocumentException("Invalid magic header: $magic")
            }

            return try {
                DataInputStream(GZIPInputStream(ByteArrayInputStream(data, 4, data.size - 4))).use { dis ->
                    val title = dis.readUTF()
                    val width = dis.readDouble()
                    val height = dis.readDouble()
                    val paperName = dis.readUTF()
                    val leftMargin = dis.readDouble()
                    val topMargin = dis.readDouble()
                    val rightMargin = dis.readDouble()
                    val bottomMargin = dis.readDouble()
                    val lineSpacing = dis.readDouble()
                    val lineCount = dis.readInt()
                    val lineWidth = dis.readFloat()
                    val watermarkAlpha = dis.readFloat()
                    val showRuled = dis.readBoolean()
                    val showWatermark = dis.readBoolean()
                    val pageCount = dis.readInt()

                    if (pageCount < 0 || pageCount > 10000) {
                        throw DocumentException("Invalid page count: $pageCount")
                    }

                    val pages = mutableListOf<NotebookPage>()
                    for (i in 0 until pageCount) {
                        val index = dis.readInt()
                        val content = dis.readUTF()
                        val hasHandwriting = dis.readBoolean()
                        pages.add(NotebookPage(index = index, config = PageConfig(), content = content, hasHandwriting = hasHandwriting))
                    }

                    val paperSize = PaperSize(width, height, paperName)
                    val config = PageConfig(
                        paperSize = paperSize,
                        leftMarginMm = leftMargin,
                        topMarginMm = topMargin,
                        rightMarginMm = rightMargin,
                        bottomMarginMm = bottomMargin,
                        lineSpacingMm = lineSpacing,
                        lineCount = lineCount,
                        lineWidthPx = lineWidth,
                        watermarkAlpha = watermarkAlpha,
                        showRuledLines = showRuled,
                        showWatermark = showWatermark
                    )

                    NotebookDocument(title = title, paperSize = paperSize, pageConfig = config, pages = pages)
                }
            } catch (e: EOFException) {
                throw DocumentException("Truncated document data", e)
            } catch (e: IOException) {
                throw DocumentException("IO error during deserialization", e)
            }
        }

        /**
         * Validates that a byte array could be a valid document without fully parsing it.
         */
        fun isValidDocument(data: ByteArray): Boolean {
            if (data.size < 4) return false
            val magic = String(data.copyOfRange(0, 4))
            return magic == MAGIC
        }
    }
}

/**
 * Exception thrown when document serialization or deserialization fails.
 */
class DocumentException(
    message: String,
    cause: Throwable? = null
) : IOException(message, cause)