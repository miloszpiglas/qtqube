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
        column[r] = value.toString()
        self._columns[c] = column
        print self._columns
        if r >= self._rowCount-1:
            self._rowCount += 1
        if c >= self._columnCount-1:
            self._columnCount  += 1
        print r, self._rowCount, c, self._columnCount
            
    def value(self, index):
        r, c = index.row(), index.column()
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
    

class EditorTableModel(core.QAbstractTableModel):

    def __init__(self, schema):
        core.QAbstractTableModel.__init__(self)
        self.schema = schema
        self.matrix = Matrix()
    
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
            return v
        elif role == core.Qt.EditRole:
            return v
        return core.QVariant()

    def setData(self, index, value, role=core.Qt.EditRole):
        self.beginResetModel()
        self.matrix.setValue(index, value)
        self.endResetModel()
        self.dataChanged.emit(index, index)
        return True
        
class QtQube(gui.QWidget):
    
    def __init__(self, schema, parent=None):
        gui.QWidget.__init__(self, parent=parent)
        self.setLayout(gui.QVBoxLayout(self))
        tableView = gui.QTableView()
        self.layout().addWidget(tableView)
        model = EditorTableModel(schema)
        tableView.setModel(model)
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
