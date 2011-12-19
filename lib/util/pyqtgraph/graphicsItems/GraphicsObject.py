from pyqtgraph.Qt import QtGui, QtCore  
from pyqtgraph.GraphicsScene import GraphicsScene
from pyqtgraph.Point import Point
import weakref

__all__ = ['GraphicsObject']
class GraphicsObject(QtGui.QGraphicsObject):
    """Extends QGraphicsObject with a few important functions. 
    (Most of these assume that the object is in a scene with a single view)
    
    This class also generates a cache of the Qt-internal addresses of each item
    so that GraphicsScene.items() can return the correct objects (this is a PyQt bug)
    """
    
    
    def __init__(self, *args):
        QtGui.QGraphicsObject.__init__(self, *args)
        self._viewWidget = None
        self._viewBox = None
        GraphicsScene.registerObject(self)  ## workaround for pyqt bug in graphicsscene.items()
    
    def getViewWidget(self):
        """Return the view widget for this item. If the scene has multiple views, only the first view is returned.
        The return value is cached; clear the cached value with forgetViewWidget()"""
        if self._viewWidget is None:
            scene = self.scene()
            if scene is None:
                return None
            views = scene.views()
            if len(views) < 1:
                return None
            self._viewWidget = weakref.ref(self.scene().views()[0])
        return self._viewWidget()
        
    def forgetViewWidget(self):
        self._viewWidget = None
        
    def getViewBox(self):
        """Return the first ViewBox or GraphicsView which bounds this item's visible space.
        If this item is not contained within a ViewBox, then the GraphicsView is returned.
        If the item is contained inside nested ViewBoxes, then the inner-most ViewBox is returned.
        The result is cached; clear the cache with forgetViewBox()
        """
        if self._viewBox is None:
            p = self
            while True:
                p = p.parentItem()
                if p is None:
                    vb = self.getViewWidget()
                    if vb is None:
                        return None
                    else:
                        self._viewBox = weakref.ref(vb)
                        break
                if hasattr(p, 'implements') and p.implements('ViewBox'):
                    self._viewBox = weakref.ref(p)
                    break
                    
        return self._viewBox()  ## If we made it this far, _viewBox is definitely not None

    def forgetViewBox(self):
        self._viewBox = None
        
        
    def deviceTransform(self, viewportTransform=None):
        """Return the transform that converts item coordinates to device coordinates (usually pixels).
        Extends deviceTransform to automatically determine the viewportTransform.
        """
        if viewportTransform is None:
            view = self.getViewWidget()
            if view is None:
                return None
            viewportTransform = view.viewportTransform()
        return QtGui.QGraphicsObject.deviceTransform(self, viewportTransform)
        
    def viewTransform(self):
        """Return the transform that maps from local coordinates to the item's ViewBox coordinates
        If there is no ViewBox, return the scene transform.
        Returns None if the item does not have a view."""
        view = self.getViewBox()
        if view is None:
            return None
        if hasattr(view, 'implements') and view.implements('ViewBox'):
            return self.itemTransform(view.innerSceneItem())[0]
        else:
            return self.sceneTransform()
            #return self.deviceTransform(view.viewportTransform())



    def getBoundingParents(self):
        """Return a list of parents to this item that have child clipping enabled."""
        p = self
        parents = []
        while True:
            p = p.parentItem()
            if p is None:
                break
            if p.flags() & self.ItemClipsChildrenToShape:
                parents.append(p)
        return parents
    
    def viewRect(self):
        """Return the bounds (in item coordinates) of this item's ViewBox or GraphicsWidget"""
        view = self.getViewBox()
        if view is None:
            return None
        bounds = self.mapRectFromView(view.viewRect()).normalized()
        
        ## nah.
        #for p in self.getBoundingParents():
            #bounds &= self.mapRectFromScene(p.sceneBoundingRect())
            
        return bounds
        
        
        
    def pixelVectors(self):
        """Return vectors in local coordinates representing the width and height of a view pixel."""
        vt = self.deviceTransform()
        if vt is None:
            return None
        vt = vt.inverted()[0]
        orig = vt.map(QtCore.QPointF(0, 0))
        return vt.map(QtCore.QPointF(1, 0))-orig, vt.map(QtCore.QPointF(0, 1))-orig
        
    def pixelLength(self, direction):
        """Return the length of one pixel in the direction indicated (in local coordinates)"""
        dt = self.deviceTransform()
        if dt is None:
            return None
        viewDir = Point(dt.map(direction) - dt.map(Point(0,0)))
        norm = viewDir.norm()
        dti = dt.inverted()[0]
        return Point(dti.map(norm)-dti.map(Point(0,0))).length()
        

    def pixelSize(self):
        v = self.pixelVectors()
        return (v[0].x()**2+v[0].y()**2)**0.5, (v[1].x()**2+v[1].y()**2)**0.5

    def pixelWidth(self):
        vt = self.deviceTransform()
        if vt is None:
            return 0
        vt = vt.inverted()[0]
        return Point(vt.map(QtCore.QPointF(1, 0))-vt.map(QtCore.QPointF(0, 0))).length()
        
    def pixelHeight(self):
        vt = self.deviceTransform()
        if vt is None:
            return 0
        vt = vt.inverted()[0]
        return Point(vt.map(QtCore.QPointF(0, 1))-vt.map(QtCore.QPointF(0, 0))).length()
        
        

    def mapToView(self, obj):
        vt = self.viewTransform()
        if vt is None:
            return None
        return vt.map(obj)
        
    def mapRectToView(self, obj):
        vt = self.viewTransform()
        if vt is None:
            return None
        return vt.mapRect(obj)
        
    def mapFromView(self, obj):
        vt = self.viewTransform()
        if vt is None:
            return None
        vt = vt.inverted()[0]
        return vt.map(obj)

    def mapRectFromView(self, obj):
        vt = self.viewTransform()
        if vt is None:
            return None
        vt = vt.inverted()[0]
        return vt.mapRect(obj)

    def pos(self):
        return Point(QtGui.QGraphicsObject.pos(self))
    
    #def itemChange(self, change, value):
        #ret = QtGui.QGraphicsObject.itemChange(self, change, value)
        #if change == self.ItemParentHasChanged or change == self.ItemSceneHasChanged:
            #print "Item scene changed:", self
            #self.setChildScene(self)  ## This is bizarre. 
        #return ret
    
    #def setChildScene(self, ch):
        #scene = self.scene()
        #for ch2 in ch.childItems():
            #if ch2.scene() is not scene:
                #print "item", ch2, "has different scene:", ch2.scene(), scene
                #scene.addItem(ch2)
                #QtGui.QApplication.processEvents()
                #print "   --> ", ch2.scene()
            #self.setChildScene(ch2)
            
    def parentItem(self):
        ## PyQt bug -- some items are returned incorrectly.
        return GraphicsScene.translateGraphicsItem(QtGui.QGraphicsObject.parentItem(self))
        
    
    def childItems(self):
        ## PyQt bug -- some child items are returned incorrectly.
        return map(GraphicsScene.translateGraphicsItem, QtGui.QGraphicsObject.childItems(self))


    def sceneTransform(self):
        ## Qt bug: do no allow access to sceneTransform() until 
        ## the item has a scene.
        
        if self.scene() is None:
            return self.transform()
        else:
            return QtGui.QGraphicsObject.sceneTransform(self)
