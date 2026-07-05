from pyModeS978._uncertainty import derive


def test_nacp_self_contained_lookup():
    result = derive(nic=0, nic_supplement_a=False, nac_p=11, nac_v=0, sil=0)
    assert result["position_accuracy_epu_m"] == 3
    assert result["position_accuracy_vepu_m"] == 4


def test_nacp_reserved_value_is_none():
    result = derive(nic=0, nic_supplement_a=False, nac_p=12, nac_v=0, sil=0)
    assert result["position_accuracy_epu_m"] is None
    assert result["position_accuracy_vepu_m"] is None


def test_nacv_self_contained_lookup():
    result = derive(nic=0, nic_supplement_a=False, nac_p=0, nac_v=4, sil=0)
    assert result["velocity_accuracy_hfom_ms"] == 0.3
    assert result["velocity_accuracy_vfom_ms"] == 0.46


def test_nacv_reserved_value_is_none():
    result = derive(nic=0, nic_supplement_a=False, nac_p=0, nac_v=5, sil=0)
    assert result["velocity_accuracy_hfom_ms"] is None
    assert result["velocity_accuracy_vfom_ms"] is None


def test_sil_probability_lookup():
    result = derive(nic=0, nic_supplement_a=False, nac_p=0, nac_v=0, sil=3)
    assert result["sil_probability_horizontal"] == 1e-7
    assert result["sil_probability_vertical"] == 2e-7


def test_sil_zero_is_none():
    result = derive(nic=0, nic_supplement_a=False, nac_p=0, nac_v=0, sil=0)
    assert result["sil_probability_horizontal"] is None
    assert result["sil_probability_vertical"] is None


def test_nic_containment_radius_with_matching_supplement():
    result = derive(nic=11, nic_supplement_a=False, nac_p=0, nac_v=0, sil=0)
    assert result["position_containment_radius_m"] == 7.5
    assert result["position_vpl_m"] == 11


def test_nic_requires_specific_supplement_value():
    # nic=9 is only defined in the table for nic_supplement_a=1, not 0.
    result = derive(nic=9, nic_supplement_a=True, nac_p=0, nac_v=0, sil=0)
    assert result["position_containment_radius_m"] == 75
    assert result["position_vpl_m"] == 112

    result_wrong_supplement = derive(nic=9, nic_supplement_a=False, nac_p=0, nac_v=0, sil=0)
    assert result_wrong_supplement["position_containment_radius_m"] is None


def test_nic_both_supplement_values_defined():
    result_0 = derive(nic=6, nic_supplement_a=False, nac_p=0, nac_v=0, sil=0)
    assert result_0["position_containment_radius_m"] == 926

    result_1 = derive(nic=6, nic_supplement_a=True, nac_p=0, nac_v=0, sil=0)
    assert result_1["position_containment_radius_m"] == 1111


def test_nic_zero_is_none():
    result = derive(nic=0, nic_supplement_a=False, nac_p=0, nac_v=0, sil=0)
    assert result["position_containment_radius_m"] is None
    assert result["position_vpl_m"] is None
