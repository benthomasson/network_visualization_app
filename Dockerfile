FROM registry.access.redhat.com/ubi8/python-39

WORKDIR $HOME/network_visualization_app
COPY . $WORKDIR

USER $USER_ID
RUN pip install .
CMD ["uvicorn" , "network_visualization_app.app:app", "--host", "0.0.0.0", "--port", "8000"]
