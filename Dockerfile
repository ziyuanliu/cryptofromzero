FROM python:3.6.2
ADD requirements.txt ./
RUN pip install -r requirements.txt
ADD mini_core ./mini_core

CMD ["python", "-m", "mini_core.__init__"]