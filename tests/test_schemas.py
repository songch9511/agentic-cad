from cadx.demos import pan_tilt_2axis
from cadx.schemas import BOM, ProductSpec


def test_demo_spec_and_bom_validate():
    spec = pan_tilt_2axis.product_spec()
    bom = pan_tilt_2axis.bom()
    assert isinstance(spec, ProductSpec)
    assert isinstance(bom, BOM)
    assert spec.id == bom.product_spec_id
    assert len(bom.generated_custom_parts) == 3
