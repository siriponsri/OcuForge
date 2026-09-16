import pytest
import torch

from eyes_detected.ordinal.corn import CORNHead, class_probabilities, encode, loss, predict


def test_corn_encoding_marks_conditional_eligibility():
    targets, eligible = encode(torch.arange(5))
    assert torch.equal(targets, torch.tensor([[0, 0, 0, 0], [1, 0, 0, 0], [1, 1, 0, 0], [1, 1, 1, 0], [1, 1, 1, 1]], dtype=torch.float))
    assert torch.equal(eligible, torch.tensor([[1, 0, 0, 0], [1, 1, 0, 0], [1, 1, 1, 0], [1, 1, 1, 1], [1, 1, 1, 1]], dtype=torch.bool))


def test_corn_head_shapes_loss_and_monotone_decode():
    head = CORNHead(8)
    logits = head(torch.randn(5, 8))
    value = loss(logits, torch.arange(5))
    value.backward()
    grades, probabilities = predict(logits.detach())
    assert logits.shape == (5, 4)
    assert torch.all(probabilities[:, 1:] <= probabilities[:, :-1])
    assert torch.allclose(class_probabilities(probabilities).sum(1), torch.ones(5))
    assert grades.min() >= 0 and grades.max() <= 4


def test_corn_rejects_wrong_shape():
    with pytest.raises(ValueError):
        encode(torch.tensor([[1]]))
    with pytest.raises(ValueError):
        predict(torch.zeros(2, 5))
