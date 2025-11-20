param(
    # Whether the output should go to env_production instead of env_development
    [switch]$Prod
)

Push-Location
Set-Location -Path $PSScriptRoot

$openApiUrl = Read-Host "Enter the url of the openAPI JSON specification"
$swaggerCodeGenVersion = "3.0.57"
$swaggerCodeGenJar = "swagger-codegen-cli-$swaggerCodeGenVersion.jar"
$packageNamePart1 = "add_to_cartovista"
$packageNamePart2 = "swagger_client"
$packageName = "$packageNamePart1.$packageNamePart2"

If (!(Test-Path -path "./$($swaggerCodeGenJar)" -PathType Leaf)) {
    Invoke-WebRequest -OutFile $swaggerCodeGenJar "https://repo1.maven.org/maven2/io/swagger/codegen/v3/swagger-codegen-cli/$swaggerCodeGenVersion/swagger-codegen-cli-$swaggerCodeGenVersion.jar"
}
java -DmodelTests=false -DmodelDocs=false -DapiTests=false -DapiDocs=false -jar $swaggerCodeGenJar generate -i $openApiUrl "-DpackageName=$packageName" -l python -o ../generatedCodeTempFolder
#If (Test-Path -path ./swagger_client) {
#   Remove-Item -Path ./swagger_client -Recurse
#}


$ApiClientFilePath = "../generatedCodeTempFolder/$packageNamePart1/$packageNamePart2/api_client.py"
$ApiClientFileContent = Get-Content -Path $ApiClientFilePath -Raw


$ApiClientFileContent = $ApiClientFileContent.Replace("from multiprocessing.pool import ThreadPool", "") 
$ApiClientFileContent = $ApiClientFileContent.Replace("self.pool = ThreadPool()", "") 
$ApiClientFileContent = $ApiClientFileContent.Replace("self.pool.close()", "") 
$ApiClientFileContent = $ApiClientFileContent.Replace("self.pool.join()", "pass") 

$ApiClientFileContent = $ApiClientFileContent -Replace "thread\s*=\sself\.pool\.apply_async\(([^\(\)]*(\([^\(\)]*\))*)*\)", "raise NotImplementedError('Async requests use multiprocessing which breaks the CartoVista QGIS plugin')"
                                         
$ApiClientFileContent | Set-Content -Path $ApiClientFilePath -NoNewline

If (Test-Path -path "./$packageNamePart2") {
    Remove-Item -Path "./$packageNamePart2" -Recurse -Force
}

$destinationPath = $Prod ? "../env_production" : "../env_development"
if (-not (Test-Path $destinationPath)) {
        New-Item -Path $destinationPath -ItemType Directory -Force | Out-Null
}
Remove-Item -Path "$destinationPath/$packageNamePart2" -Recurse
Move-Item -Path "../generatedCodeTempFolder/$packageNamePart1/$packageNamePart2" $destinationPath -Force
Remove-Item -Path ../generatedCodeTempFolder -Recurse

Pop-Location
