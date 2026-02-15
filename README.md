**Command：**

```bash
mkdir -p /coursegrader
cd compiler
ln -s $(pwd)/test/pagedattn/testdata /coursegrader/testdata 
ln -s $(pwd)/test/pagedattn/submits/stu /coursegrader/submit
export PYGRADING_DEBUG=true
python3 manage.py package
python kernel.pyz > output.txt
```
