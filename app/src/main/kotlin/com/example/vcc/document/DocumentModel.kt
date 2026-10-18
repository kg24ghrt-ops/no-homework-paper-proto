package com.example.vcc.document

import android.os Parcel
import android.os.Parcelable
import java.io.Serializable

/**
 * Represents a paper size with dimensions in millimeters.
 */
data class PaperSize(
    val widthMm: Double,
    val heightMm: Double,
    val name: String
) : Serializable {
    companion object {
        val B5 = PaperSize(176.0, 250.0, "B5")
        val A4 = PaperSize(210.0, 297.0, "A4")
        val A5 = PaperSize(148.0, 210.0, "A5")

        val DEFAULT = B5

        fun fromName(name: String): PaperSize {
            return when (name.uppercase()) {
                "A4" -> A4
                "A5" -> A5
                else -> B5
            }
        }
    }
}

/**
 * Configuration for page layout including margins and line spacing.
 */
data class PageConfig(
    val paperSize: PaperSize = PaperSize.B5,
    val leftMarginMm: Double = 20.0,
    val topMarginMm: Double = 20.0,
    val rightMarginMm: Double = 20.0,
    val bottomMarginMm: Double = 20.0,
    val lineSpacingMm: Double = 8.0,
    val lineCount: Int = 0,  // 0 = auto-compute
    val lineWidthPx: Float = 1.0f,
    val watermarkAlpha: Float = 0.1f,
    val showRuledLines: Boolean = true,
    val showWatermark: Boolean = true
) : Serializable {
    /**
     * Computes the content rectangle in mm.
     */
    fun contentRectMm(): ContentRect {
        return ContentRect(
            left = leftMarginMm,
            top = topMarginMm,
            right = paperSize.widthMm - rightMarginMm,
            bottom = paperSize.heightMm - bottomMarginMm
        )
    }

    /**
     * Computes the number of ruled lines that fit on the page.
     */
    fun computeLineCount(): Int {
        if (lineCount > 0) return lineCount
        val content = contentRectMm()
        val availableHeight = content.bottom - content.top
        val count = (availableHeight / lineSpacingMm).toInt()
        return maxOf(1, count)
    }

    /**
     * Converts mm to pixels at a given density (DPI).
     */
    fun mmToPx(mm: Double, densityDpi: Double): Double {
        return mm * densityDpi / 25.4
    }

    /**
     * Validates that the configuration is sane.
     */
    fun validate(): ValidationResult {
        val errors = mutableListOf<String>()

        if (paperSize.widthMm <= 0) {
            errors.add("Paper width must be positive")
        }
        if (paperSize.heightMm <= 0) {
            errors.add("Paper height must be positive")
        }
        if (leftMarginMm < 0 || topMarginMm < 0 || rightMarginMm < 0 || bottomMarginMm < 0) {
            errors.add("Margins cannot be negative")
        }
        if (leftMarginMm + rightMarginMm >= paperSize.widthMm) {
            errors.add("Horizontal margins exceed paper width")
        }
        if (topMarginMm + bottomMarginMm >= paperSize.heightMm) {
            errors.add("Vertical margins exceed paper height")
        }
        if (lineSpacingMm <= 0) {
            errors.add("Line spacing must be positive")
        }
        if (watermarkAlpha < 0f || watermarkAlpha > 1f) {
            errors.add("Watermark alpha must be between 0 and 1")
        }

        return ValidationResult(errors.isEmpty(), errors)
    }
}

/**
 * A rectangle defined by left, top, right, bottom in mm.
 */
data class ContentRect(
    val left: Double,
    val top: Double,
    val right: Double,
    val bottom: Double
) {
    val width: Double get() = right - left
    val height: Double get() = bottom - top

    fun contains(x: Double, y: Double): Boolean {
        return x >= left && x <= right && y >= top && y <= bottom
    }
}

/**
 * Result of configuration validation.
 */
data class ValidationResult(
    val isValid: Boolean,
    val errors: List<String>
)

/**
 * Represents a single page in a notebook document.
 */
data class NotebookPage(
    val index: Int,
    val config: PageConfig,
    val content: String = "",
    val hasHandwriting: Boolean = false
) : Serializable {
    companion object {
        fun empty(index: Int, config: PageConfig): NotebookPage {
            return NotebookPage(index = index, config = config)
        }
    }
}

/**
 * Represents a notebook document containing multiple pages.
 */
data class NotebookDocument(
    val title: String,
    val paperSize: PaperSize = PaperSize.B5,
    val pageConfig: PageConfig = PageConfig(),
    val pages: List<NotebookPage> = emptyList()
) : Serializable {
    val pageCount: Int get() = pages.size

    fun getPage(index: Int): NotebookPage? {
        return if (index in pages.indices) pages[index] else null
    }

    fun withPage(index: Int, content: String, hasHandwriting: Boolean = false): NotebookDocument {
        val newPages = pages.toMutableList()
        if (index < newPages.size) {
            newPages[index] = newPages[index].copy(content = content, hasHandwriting = hasHandwriting)
        }
        return copy(pages = newPages)
    }

    fun addPage(): NotebookDocument {
        val newPage = NotebookPage.empty(pages.size, pageConfig)
        return copy(pages = pages + newPage)
    }

    companion object {
        fun empty(title: String = "Untitled", paperSize: PaperSize = PaperSize.B5): NotebookDocument {
            val config = PageConfig(paperSize = paperSize)
            val firstPage = NotebookPage.empty(0, config)
            return NotebookDocument(
                title = title,
                paperSize = paperSize,
                pageConfig = config,
                pages = listOf(firstPage)
            )
        }
    }
}