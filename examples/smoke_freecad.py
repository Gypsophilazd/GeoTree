"""Synthetic local CAD, no model, benchmark data or verifier."""
import hashlib
import tempfile
from pathlib import Path

import FreeCAD as App
import Part

from geotree.constraint_candidates import digest, extract_text
from geotree.evidence_gate import verify_document
from geotree.geometry_observer import inspect_file
from geotree.safe_repair import RepairRequest, attempt_pad_length


def main(root):
    source = root / "smoke.FCStd"
    doc = App.newDocument("Smoke")
    body = doc.addObject("PartDesign::Body", "Body")
    sketch = body.newObject("Sketcher::SketchObject", "Profile")
    pts = [App.Vector(x, y, 0) for x, y in [(0, 0), (20, 0), (20, 10), (0, 10)]]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        sketch.addGeometry(Part.LineSegment(a, b), False)
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sketch
    pad.Length = 9
    doc.recompute()
    assert body.Shape.isValid() and len(body.Shape.Solids) == 1
    doc.saveAs(str(source))
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    public = "Set Pad.Length to 12 mm."
    candidates = extract_text(public)
    assert len(candidates) == 1, candidates
    pre = verify_document(doc, public, candidates, sha)
    assert pre["results"][0]["hard_fail"], pre
    App.closeDocument(doc.Name)
    print("Geometry observation:", inspect_file(source, root))
    req = RepairRequest(sha, digest(public), candidates[0].constraint_id, "SET_ISOLATED_PAD_LENGTH", "Pad")
    result = attempt_pad_length(source, root, public, req)
    assert result["status"] == "VERIFIED", result
    assert result["post"]["results"][0]["status"] == "PASS", result
    assert max(result["outside_mm3"]) <= 1e-5
    assert hashlib.sha256(source.read_bytes()).hexdigest() == sha
    rejected = attempt_pad_length(source, root, public, RepairRequest("0" * 64, req.public_sha256,
        req.constraint_id, req.operation, req.target_feature))
    assert rejected["status"] == "REJECTED" and rejected["reason"] == "hash_mismatch"
    print("PASS FreeCAD", ".".join(App.Version()[:3]), "GeometryObserver; hard FAIL -> verified PASS; original unchanged; wrong SHA rejected")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="geotree-smoke-") as work:
        main(Path(work))
