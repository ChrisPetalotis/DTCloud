FROM rstudio/plumber

RUN apt-get update -qq && apt-get install -y \
      libssl-dev \
      libcurl4-gnutls-dev \
      libudunits2-dev \
      gdal-bin \
      libgdal-dev \
      && apt-get clean \
      && rm -rf /var/lib/apt/lists/ 

RUN R -e 'install.packages(c("sdm", "dismo"))'

COPY / /

EXPOSE 80

ENTRYPOINT ["R", "-e", "r = plumber::plumb('api.R'); r$run(port = 80, host = '0.0.0.0')"]