# qtqube

from PyQt4 import QtCore as core
from PyQt4 import QtGui as gui
from pyqube import pyqube as p
from pyqube import views as v


class Matrix(object):

    def __init__(self):
        self._labels = [u'Attribute', u'Alias', u'Sort', u'Visible', u'Function', u'Condition', u'Or']
        self._labelsCount = len(self._labels)
        self._columns = {}
        self._columnCount = 5
        self._rowCount = 7
        
    def label(self, row):
        if row < self._labelsCount:
            return self._labels[row]
        return self._labels[-1]
    
    def setValue(self, index, value):
        r, c = index.row(), index.column()
        column = self._columns.get(c, {})
        column[r] = value
        self._columns[c] = column
        print self._columns
        if r >= self._rowCount-1:
            self._rowCount += 1
        if c >= self._columnCount-1:
            self._columnCount  += 1
        print r, self._rowCount, c, self._columnCount
            
    def value(self, index):
        r, c = index.row(), index.column()
        return self.cellValue(r, c)
    
    def cellValue(self, r, c):
        column = self._columns.get(c, {})
        if r in [2, 3]:
            return column.get(r, False)
        else:
            return column.get(r, None)
    
    @property
    def rowCount(self):
        return self._rowCount
    
    @property    
    def columnCount(self):
        return self._columnCount     

class ValueConverter(object):

    def fromInput(self, text):
        return text
        
    def toOutput(self, value):
        return value
        
class AttrConverter(ValueConverter):

    def __init__(self, schema):
        ValueConverter.__init__(self)
        self.schema = schema
        
    def fromInput(self, text):
        print text
        return self.schema.attrByName(str(text))
        
    def toOutput(self, value):
        if value and isinstance(value, v.ViewAttr):
            return value.fullName()    
        elif value:
            return value
        else:
            return None
            
class AttrValidator(gui.QValidator):
    
    def __init__(self, schema, parent=None):
        gui.QValidator.__init__(self, parent=parent)
        self.schema = schema
        self.viewAttrs = []
        
    def validate(self, qtext, pos):
        text = str(qtext)
        if not text:
            return (gui.QValidator.Intermediate, pos)
        elif '.' in text:
            if not self.viewAttrs:
                v =  self.schema.viewByName(text[:text.index('.')])
                if not v:
                    return (gui.QValidator.Invalid, pos)
                else:
                    self.viewAttrs = [a.realName() for a in v.viewAttrs()]
            elif len(text) > text.index('.')+1:
                attr = text[text.index('.')+1:]
                for a in self.viewAttrs:
                    if a == attr:
                        return (gui.QValidator.Acceptable, pos)
                    elif a.startswith(attr):
                        return (gui.QValidator.Intermediate, pos)
        return (gui.QValidator.Intermediate, pos)
        
        
        
class BoolConverter(ValueConverter):
    
    def __init__(self):
        ValueConverter.__init__(self)
        
    def fromInput(self, variant):
        return variant.toBool()
        
    def toOutput(self, value):
        return value
        
class StrConverter(ValueConverter):
    
    def __init__(self):
        ValueConverter.__init__(self)
        
    def fromInput(self, variant):
        return str(variant.toString())
        
    def toOutput(self, value):
        return value 

class EditorTableModel(core.QAbstractTableModel):

    def __init__(self, schema, matrix ):
        core.QAbstractTableModel.__init__(self)
        self.schema = schema
        self.matrix = matrix
        strc = StrConverter()
        boolc = BoolConverter()
        self.converters = {0:AttrConverter(self.schema), 1:strc, 2:boolc, 3:boolc, 4:strc, 5:strc, 6:strc }
    
    def _converter(self, row):
        if row < 7:
            return self.converters[row]
        else:
            return self.converters[6]
    
    def flags(self,indeks):
        return core.Qt.ItemIsEnabled | core.Qt.ItemIsEditable | core.Qt.ItemIsSelectable
        
    def headerData(self, section, orientation, role):
        if orientation == core.Qt.Vertical and role == core.Qt.DisplayRole:
            return self.matrix.label(section)
        elif orientation == core.Qt.Horizontal and role==core.Qt.DisplayRole:
            return unicode(section+1)
        else:
            return core.QVariant()
        
    def rowCount(self, model):
        return self.matrix.rowCount
        
    def columnCount(self, model):
        return self.matrix.columnCount
        
    def data(self, index, role=core.Qt.DisplayRole):
        v = self.matrix.value(index)
        if role == core.Qt.DisplayRole:
            return self._converter(index.row()).toOutput(v)
        elif role == core.Qt.EditRole:
            return self._converter(index.row()).toOutput(v)
        return core.QVariant()

    def setData(self, index, value, role=core.Qt.EditRole):
        self.beginResetModel()
        self.matrix.setValue(index, self._converter(index.row()).fromInput(value))
        self.endResetModel()
        self.dataChanged.emit(index, index)
        return True

class AttributesDelegate(gui.QStyledItemDelegate):

    def __init__(self, schema, tableView):
        gui.QStyledItemDelegate.__init__(self, parent=tableView)
        self.setItemEditorFactory(gui.QItemEditorFactory.defaultFactory())
        self.schema = schema
        self.matrix = tableView.model().matrix
        
    def _attrs(self, index):
        selected = set([])
        for c in range(self.matrix.columnCount):
            if c == index.column():
                continue
            a = self.matrix.cellValue(0, c)
            if a:
                sv = unicode(a)
                attr = self.schema.attrByName(sv)
                for view in self.schema.relatedViews(attr.view):
                    selected = selected | set([x.fullName() for x in view.viewAttrs() ])
        if selected:
            print selected
            return list(selected)
        else:
            return [a.fullName() for a in self.schema.attributes()]
        
    def createEditor(self, parent, style, index):
        self.initStyleOption(style, index)
        textField = gui.QLineEdit(parent)
        completer = gui.QCompleter(self._attrs(index))
        completer.setCaseSensitivity(core.Qt.CaseInsensitive)
        textField.setCompleter(completer)
        textField.setValidator(AttrValidator(self.schema, textField))
        return textField
        
    def setEditorData(self, editor, index):
        value = index.data().toString()
        editor.setText(value)
    
    def setModelData(self, editor, model, index):
        model.setData(index, editor.text())
        
class QtQube(gui.QWidget):
    
    def __init__(self, schema, parent=None):
        gui.QWidget.__init__(self, parent=parent)
        self.setLayout(gui.QVBoxLayout(self))
        tableView = gui.QTableView()
        self.layout().addWidget(tableView)
        matrix = Matrix()
        model = EditorTableModel(schema, matrix)
        tableView.setModel(model)
        tableView.setItemDelegateForRow(0, AttributesDelegate(schema, tableView))
        tableView.horizontalHeader().setResizeMode(gui.QHeaderView.Stretch)

def createSchema():
    booksView = v.View('books', 'Books', ['title', 'author', 'year', 'publisher', 'category'])
    publishersView = v.View('publishers', 'Publishers', ['id', 'name', 'city'])
    categoriesView = v.View('categories', 'Categories', ['id', 'category_name'])
    citiesView = v.View('cities', 'Cities', ['id', 'city_name'])
    
    bookPublisher = v.Relation(
                            [v.AttrPair
                                (booksView.attribute('publisher'), 
                                            publishersView.attribute('id')
                                )
                            ]
                            )
    publisherCity = v.Relation(
                            [v.AttrPair
                                (
                                    publishersView.attribute('city'), 
                                    citiesView.attribute('id')
                                )
                            ]
                            )
    bookCategory = v.Relation(
                           [v.AttrPair
                                (
                                    booksView.attribute('category'), 
                                    categoriesView.attribute('id')
                                )
                            ]
                            )
    schema = v.Schema()
    schema.addView(booksView)
    schema.addView(publishersView, bookPublisher)
    schema.addView(categoriesView, bookCategory)
    schema.addView(citiesView, publisherCity)
    return schema
        
def main():
    import sys
    app = gui.QApplication(sys.argv)
    dialog = gui.QDialog()
    dialog.setLayout(gui.QVBoxLayout())
    dialog.layout().addWidget(QtQube(createSchema(), dialog))
    dialog.setMinimumSize(500, 500)
    dialog.exec_()

if __name__ == '__main__':
    main()
