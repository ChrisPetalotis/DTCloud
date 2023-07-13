library(sdm)
library(dismo)

m_merged_GrW=read.sdm("merged_GrW_all2.sdm")

#* @get /sdmhealth
function() {
  return('')
}

#' @post /predictions 
function(df){
  data = df
  column_list <- list()
  for (inner_list in data) {
    # Transform the inner list to a column and append it to the column list
    column_list <- c(column_list, list(unlist(inner_list)))
  }
  presabs <- as.data.frame(column_list)
  
  # Set the column names
  colnames(presabs) <- names(data)
  
  mydata_clean2=presabs
  coordinates(mydata_clean2)=~x+y
  proj4string(mydata_clean2)<- CRS("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel +units=m +no_defs")
  mydata_clean= as(mydata_clean2, "data.frame")
  longs <- mydata_clean$x
  lats <- mydata_clean$y
  mydata_clean <- subset(mydata_clean, select = -x)
  mydata_clean <- subset(mydata_clean, select = -y)
  predictions <- predict(m_merged_GrW, mydata_clean, mean=TRUE)
  return(predictions)
}


