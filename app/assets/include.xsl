<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs"
    version="1.0">
    <xsl:output encoding="UTF-8" method="html"/>

    <xsl:template match="results">
        <div>
            <h3>Results</h3>
            <p><xsl:value-of select="count(//div)"/> results</p>
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="div">
        <form class="annotation-container" method="POST">
            <h4>Result <xsl:value-of select="count(preceding::div) + 1"/></h4>
            <div class="row">
                <div class="col-md-2">
                    <button class="btn btn-primary" type="submit">Save</button>
                    <br /><br/>
                    <button class="btn btn-secondary" type="reset">Reset</button>
                </div>
                <div class="col-md-10">
                   <xsl:apply-templates select="bibl" />
                   <div>
                       <xsl:apply-templates select=".//w" />
                   </div>
                   <div>
                       <textarea style="width:100%; height: 150px;" name="xml"><xsl:copy-of select="." /></textarea>
                   </div>
               </div>
            </div>
            <hr/>
        </form>
    </xsl:template>

    <xsl:template match="w">
        <xsl:choose>
            <xsl:when test="@ana">
                <em style="color:red;"><xsl:apply-templates/></em><span class="color:grey;">[<xsl:value-of select="@lemma" />]</span>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text> </xsl:text>
    </xsl:template>

    <xsl:template match="bibl">
        <div><xsl:apply-templates /></div>
    </xsl:template>

    <xsl:template match="title">
        <i><xsl:apply-templates /></i>
    </xsl:template>

    <xsl:template match="author">
        <b><xsl:apply-templates /></b>
    </xsl:template>

    <xsl:template match="biblScope">
        <xsl:apply-templates />
    </xsl:template>

</xsl:stylesheet>