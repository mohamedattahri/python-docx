# encoding: utf-8

"""
Custom element classes for tables
"""

from __future__ import absolute_import, print_function, unicode_literals

from . import parse_xml
from ..exceptions import InvalidSpanError
from .ns import nsdecls
from ..shared import Emu, Twips
from .simpletypes import (
    ST_Merge, ST_TblLayoutType, ST_TblWidth, ST_TwipsMeasure, XsdInt
)
from .xmlchemy import (
    BaseOxmlElement, OneAndOnlyOne, OneOrMore, OptionalAttribute,
    RequiredAttribute, ZeroOrOne, ZeroOrMore
)


class CT_Row(BaseOxmlElement):
    """
    ``<w:tr>`` element
    """
    tc = ZeroOrMore('w:tc')

    def tc_at_grid_col(self, idx):
        """
        The ``<w:tc>`` element appearing at grid column *idx*. Raises
        |ValueError| if no ``w:tc`` element begins at that grid column.
        """
        grid_col = 0
        for tc in self.tc_lst:
            if grid_col == idx:
                return tc
            grid_col += tc.grid_span
            if grid_col > idx:
                raise ValueError('no cell on grid column %d' % idx)
        raise ValueError('index out of bounds')

    @property
    def tr_idx(self):
        """
        The index of this ``<w:tr>`` element within its parent ``<w:tbl>``
        element.
        """
        return self.getparent().tr_lst.index(self)

    def _new_tc(self):
        return CT_Tc.new()


class CT_Tbl(BaseOxmlElement):
    """
    ``<w:tbl>`` element
    """
    tblPr = OneAndOnlyOne('w:tblPr')
    tblGrid = OneAndOnlyOne('w:tblGrid')
    tr = ZeroOrMore('w:tr')

    def iter_tcs(self):
        """
        Generate each of the `w:tc` elements in this table, left to right and
        top to bottom. Each cell in the first row is generated, followed by
        each cell in the second row, etc.
        """
        for tr in self.tr_lst:
            for tc in tr.tc_lst:
                yield tc

    @classmethod
    def new(cls):
        """
        Return a new ``<w:tbl>`` element, containing the required
        ``<w:tblPr>`` and ``<w:tblGrid>`` child elements.
        """
        tbl = parse_xml(cls._tbl_xml())
        return tbl

    @property
    def col_count(self):
        """
        The number of grid columns in this table.
        """
        return len(self.tblGrid.gridCol_lst)

    @classmethod
    def _tbl_xml(cls):
        return (
            '<w:tbl %s>\n'
            '  <w:tblPr>\n'
            '    <w:tblW w:type="auto" w:w="0"/>\n'
            '  </w:tblPr>\n'
            '  <w:tblGrid/>\n'
            '</w:tbl>' % nsdecls('w')
        )


class CT_TblGrid(BaseOxmlElement):
    """
    ``<w:tblGrid>`` element, child of ``<w:tbl>``, holds ``<w:gridCol>``
    elements that define column count, width, etc.
    """
    gridCol = ZeroOrMore('w:gridCol', successors=('w:tblGridChange',))


class CT_TblGridCol(BaseOxmlElement):
    """
    ``<w:gridCol>`` element, child of ``<w:tblGrid>``, defines a table
    column.
    """
    w = OptionalAttribute('w:w', ST_TwipsMeasure)

    @property
    def gridCol_idx(self):
        """
        The index of this ``<w:gridCol>`` element within its parent
        ``<w:tblGrid>`` element.
        """
        return self.getparent().gridCol_lst.index(self)


class CT_TblLayoutType(BaseOxmlElement):
    """
    ``<w:tblLayout>`` element, specifying whether column widths are fixed or
    can be automatically adjusted based on content.
    """
    type = OptionalAttribute('w:type', ST_TblLayoutType)


class CT_TblPr(BaseOxmlElement):
    """
    ``<w:tblPr>`` element, child of ``<w:tbl>``, holds child elements that
    define table properties such as style and borders.
    """
    tblStyle = ZeroOrOne('w:tblStyle', successors=(
        'w:tblpPr', 'w:tblOverlap', 'w:bidiVisual', 'w:tblStyleRowBandSize',
        'w:tblStyleColBandSize', 'w:tblW', 'w:jc', 'w:tblCellSpacing',
        'w:tblInd', 'w:tblBorders', 'w:shd', 'w:tblLayout', 'w:tblCellMar',
        'w:tblLook', 'w:tblCaption', 'w:tblDescription', 'w:tblPrChange'
    ))
    tblLayout = ZeroOrOne('w:tblLayout', successors=(
        'w:tblLayout', 'w:tblCellMar', 'w:tblLook', 'w:tblCaption',
        'w:tblDescription', 'w:tblPrChange'
    ))

    @property
    def autofit(self):
        """
        Return |False| if there is a ``<w:tblLayout>`` child with ``w:type``
        attribute set to ``'fixed'``. Otherwise return |True|.
        """
        tblLayout = self.tblLayout
        if tblLayout is None:
            return True
        return False if tblLayout.type == 'fixed' else True

    @autofit.setter
    def autofit(self, value):
        tblLayout = self.get_or_add_tblLayout()
        tblLayout.type = 'autofit' if value else 'fixed'

    @property
    def style(self):
        """
        Return the value of the ``val`` attribute of the ``<w:tblStyle>``
        child or |None| if not present.
        """
        tblStyle = self.tblStyle
        if tblStyle is None:
            return None
        return tblStyle.val

    @style.setter
    def style(self, value):
        self._remove_tblStyle()
        if value is None:
            return
        self._add_tblStyle(val=value)


class CT_TblWidth(BaseOxmlElement):
    """
    Used for ``<w:tblW>`` and ``<w:tcW>`` elements and many others, to
    specify a table-related width.
    """
    # the type for `w` attr is actually ST_MeasurementOrPercent, but using
    # XsdInt for now because only dxa (twips) values are being used. It's not
    # entirely clear what the semantics are for other values like -01.4mm
    w = RequiredAttribute('w:w', XsdInt)
    type = RequiredAttribute('w:type', ST_TblWidth)

    @property
    def width(self):
        """
        Return the EMU length value represented by the combined ``w:w`` and
        ``w:type`` attributes.
        """
        if self.type != 'dxa':
            return None
        return Twips(self.w)

    @width.setter
    def width(self, value):
        self.type = 'dxa'
        self.w = Emu(value).twips


class CT_Tc(BaseOxmlElement):
    """
    ``<w:tc>`` table cell element
    """
    tcPr = ZeroOrOne('w:tcPr')  # bunches of successors, overriding insert
    p = OneOrMore('w:p')
    tbl = OneOrMore('w:tbl')

    @property
    def bottom(self):
        """
        The row index that marks the bottom extent of the vertical span of
        this cell. This is one greater than the index of the bottom-most row
        of the span, similar to how a slice of the cell's rows would be
        specified.
        """
        if self.vMerge is not None:
            tc_below = self._tc_below
            if tc_below is not None and tc_below.vMerge == ST_Merge.CONTINUE:
                return tc_below.bottom
        return self._tr_idx + 1

    def clear_content(self):
        """
        Remove all content child elements, preserving the ``<w:tcPr>``
        element if present. Note that this leaves the ``<w:tc>`` element in
        an invalid state because it doesn't contain at least one block-level
        element. It's up to the caller to add a ``<w:p>``child element as the
        last content element.
        """
        new_children = []
        tcPr = self.tcPr
        if tcPr is not None:
            new_children.append(tcPr)
        self[:] = new_children

    @property
    def grid_span(self):
        """
        The integer number of columns this cell spans. Determined by
        ./w:tcPr/w:gridSpan/@val, it defaults to 1.
        """
        tcPr = self.tcPr
        if tcPr is None:
            return 1
        return tcPr.grid_span

    @property
    def left(self):
        """
        The grid column index at which this ``<w:tc>`` element appears.
        """
        return self._grid_col

    def merge(self, other_tc):
        """
        Return the top-left ``<w:tc>`` element of a new span formed by
        merging the rectangular region defined by using this tc element and
        *other_tc* as diagonal corners.
        """
        top, left, height, width = self._span_dimensions(other_tc)
        top_tc = self._tbl.tr_lst[top].tc_at_grid_col(left)
        top_tc._grow_to(width, height)
        return top_tc

    @classmethod
    def new(cls):
        """
        Return a new ``<w:tc>`` element, containing an empty paragraph as the
        required EG_BlockLevelElt.
        """
        return parse_xml(
            '<w:tc %s>\n'
            '  <w:p/>\n'
            '</w:tc>' % nsdecls('w')
        )

    @property
    def right(self):
        """
        The grid column index that marks the right-side extent of the
        horizontal span of this cell. This is one greater than the index of
        the right-most column of the span, similar to how a slice of the
        cell's columns would be specified.
        """
        return self._grid_col + self.grid_span

    @property
    def top(self):
        """
        The top-most row index in the vertical span of this cell.
        """
        if self.vMerge is None or self.vMerge == ST_Merge.RESTART:
            return self._tr_idx
        return self._tc_above.top

    @property
    def vMerge(self):
        """
        The value of the ./w:tcPr/w:vMerge/@val attribute, or |None| if the
        w:vMerge element is not present.
        """
        tcPr = self.tcPr
        if tcPr is None:
            return None
        return tcPr.vMerge_val

    @property
    def width(self):
        """
        Return the EMU length value represented in the ``./w:tcPr/w:tcW``
        child element or |None| if not present.
        """
        tcPr = self.tcPr
        if tcPr is None:
            return None
        return tcPr.width

    @width.setter
    def width(self, value):
        tcPr = self.get_or_add_tcPr()
        tcPr.width = value

    @property
    def _grid_col(self):
        """
        The grid column at which this cell begins.
        """
        tr = self._tr
        idx = tr.tc_lst.index(self)
        preceding_tcs = tr.tc_lst[:idx]
        return sum(tc.grid_span for tc in preceding_tcs)

    def _grow_to(self, width, height, top_tc=None):
        """
        Grow this cell to *width* grid columns and *height* rows by expanding
        horizontal spans and creating continuation cells to form vertical
        spans.
        """
        raise NotImplementedError

    def _insert_tcPr(self, tcPr):
        """
        ``tcPr`` has a bunch of successors, but it comes first if it appears,
        so just overriding and using insert(0, ...) rather than spelling out
        successors.
        """
        self.insert(0, tcPr)
        return tcPr

    def _new_tbl(self):
        return CT_Tbl.new()

    def _span_dimensions(self, other_tc):
        """
        Return a (top, left, height, width) 4-tuple specifying the extents of
        the merged cell formed by using this tc and *other_tc* as opposite
        corner extents.
        """
        def raise_on_inverted_L(a, b):
            if a.top == b.top and a.bottom != b.bottom:
                raise InvalidSpanError('requested span not rectangular')
            if a.left == b.left and a.right != b.right:
                raise InvalidSpanError('requested span not rectangular')

        def raise_on_tee_shaped(a, b):
            top_most, other = (a, b) if a.top < b.top else (b, a)
            if top_most.top < other.top and top_most.bottom > other.bottom:
                raise InvalidSpanError('requested span not rectangular')

            left_most, other = (a, b) if a.left < b.left else (b, a)
            if left_most.left < other.left and left_most.right > other.right:
                raise InvalidSpanError('requested span not rectangular')

        raise_on_inverted_L(self, other_tc)
        raise_on_tee_shaped(self, other_tc)

        top = min(self.top, other_tc.top)
        left = min(self.left, other_tc.left)
        bottom = max(self.bottom, other_tc.bottom)
        right = max(self.right, other_tc.right)

        return top, left, bottom - top, right - left

    @property
    def _tbl(self):
        """
        The tbl element this tc element appears in.
        """
        return self.xpath('./ancestor::w:tbl')[0]

    @property
    def _tc_above(self):
        """
        The `w:tc` element immediately above this one in its grid column.
        """
        return self._tr_above.tc_at_grid_col(self._grid_col)

    @property
    def _tc_below(self):
        """
        The tc element immediately below this one in its grid column.
        """
        tr_below = self._tr_below
        if tr_below is None:
            return None
        return tr_below.tc_at_grid_col(self._grid_col)

    @property
    def _tr(self):
        """
        The tr element this tc element appears in.
        """
        return self.xpath('./ancestor::w:tr')[0]

    @property
    def _tr_above(self):
        """
        The tr element prior in sequence to the tr this cell appears in.
        Raises |ValueError| if called on a cell in the top-most row.
        """
        tr_lst = self._tbl.tr_lst
        tr_idx = tr_lst.index(self._tr)
        if tr_idx == 0:
            raise ValueError('no tr above topmost tr')
        return tr_lst[tr_idx-1]

    @property
    def _tr_below(self):
        """
        The tr element next in sequence after the tr this cell appears in, or
        |None| if this cell appears in the last row.
        """
        tr_lst = self._tbl.tr_lst
        tr_idx = tr_lst.index(self._tr)
        try:
            return tr_lst[tr_idx+1]
        except IndexError:
            return None

    @property
    def _tr_idx(self):
        """
        The row index of the tr element this tc element appears in.
        """
        return self._tbl.tr_lst.index(self._tr)


class CT_TcPr(BaseOxmlElement):
    """
    ``<w:tcPr>`` element, defining table cell properties
    """
    _tag_seq = (
        'w:cnfStyle', 'w:tcW', 'w:gridSpan', 'w:hMerge', 'w:vMerge',
        'w:tcBorders', 'w:shd', 'w:noWrap', 'w:tcMar', 'w:textDirection',
        'w:tcFitText', 'w:vAlign', 'w:hideMark', 'w:headers', 'w:cellIns',
        'w:cellDel', 'w:cellMerge', 'w:tcPrChange'
    )
    tcW = ZeroOrOne('w:tcW', successors=_tag_seq[2:])
    gridSpan = ZeroOrOne('w:gridSpan', successors=_tag_seq[3:])
    vMerge = ZeroOrOne('w:vMerge', successors=_tag_seq[5:])
    del _tag_seq

    @property
    def grid_span(self):
        """
        The integer number of columns this cell spans. Determined by
        ./w:gridSpan/@val, it defaults to 1.
        """
        gridSpan = self.gridSpan
        if gridSpan is None:
            return 1
        return gridSpan.val

    @property
    def vMerge_val(self):
        """
        The value of the ./w:vMerge/@val attribute, or |None| if the
        w:vMerge element is not present.
        """
        vMerge = self.vMerge
        if vMerge is None:
            return None
        return vMerge.val

    @property
    def width(self):
        """
        Return the EMU length value represented in the ``<w:tcW>`` child
        element or |None| if not present or its type is not 'dxa'.
        """
        tcW = self.tcW
        if tcW is None:
            return None
        return tcW.width

    @width.setter
    def width(self, value):
        tcW = self.get_or_add_tcW()
        tcW.width = value


class CT_VMerge(BaseOxmlElement):
    """
    ``<w:vMerge>`` element, specifying vertical merging behavior of a cell.
    """
    val = OptionalAttribute('w:val', ST_Merge, default=ST_Merge.CONTINUE)
