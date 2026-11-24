"""No model or Benchmark calls. Use an existing Linux FreeCAD docker image."""
from tempfile import TemporaryDirectory
from pathlib import Path
from fastapi.testclient import TestClient
from . import app as mod

def main():
    with TemporaryDirectory() as tmp:
        mod.DATA = Path(tmp) / 'jobs'
        mod.DATA.mkdir()
        with TestClient(mod.app) as client:
            assert client.get('/').status_code == 200
            job = client.post('/api/jobs',json={'prompt':'No model transport test','provider':'Mock'})
            assert job.json()['mode'] == 'MOCK' and job.json()['status'] == 'done'
            inspect = client.post('/api/demo/inspect')
            assert inspect.status_code == 200, inspect.text
            measured = inspect.json()
            assert measured['status'] == 'FAIL' and measured['unique_mapping'], measured
            fixed = client.post('/api/demo/repair')
            assert fixed.status_code == 200, fixed.text
            result = fixed.json()
            assert result['status'] == 'ACCEPTED' and max(result['geometry']['outside_mm3']) < 1e-5, result
            assert client.get(result['previews']['after']['url']).status_code == 200
            print(f"PASS Mock transport, real FreeCAD {measured['measured']:.6f}° -> 90°, isolated repair, independent replay, mesh")
if __name__ == '__main__':
    main()
