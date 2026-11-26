"""Optional IFC geometry check on a fully synthetic solid."""

import pytest

ifcopenshell = pytest.importorskip("ifcopenshell")
import ifcopenshell.geom
import ifcopenshell.validate


def test_synthetic_ifc_rectangle_extrusion() -> None:
    model = ifcopenshell.file(schema="IFC4")
    point2 = model.createIfcCartesianPoint((0.0, 0.0))
    point3 = model.createIfcCartesianPoint((0.0, 0.0, 0.0))
    position2 = model.createIfcAxis2Placement2D(point2, None)
    position3 = model.createIfcAxis2Placement3D(point3, None, None)
    direction = model.createIfcDirection((0.0, 0.0, 1.0))
    profile = model.createIfcRectangleProfileDef("AREA", None, position2, 3.0, 4.0)
    solid = model.createIfcExtrudedAreaSolid(profile, position3, direction, 2.0)

    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(model, logger)
    assert not logger.statements
    shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), solid)
    vertices = shape.verts
    assert vertices
    spans = [
        max(vertices[axis::3]) - min(vertices[axis::3]) for axis in range(3)
    ]
    assert spans == pytest.approx([3.0, 4.0, 2.0])
