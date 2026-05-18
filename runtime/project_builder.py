import os
from pathlib import Path


class ProjectBuilder:

    def __init__(self):

        self.base_path = (
            "generated_projects"
        )

    def create_project_structure(
            self,
            project_name
    ):

        project_path = os.path.join(
            self.base_path,
            project_name
        )

        directories = [

            # Main Java
            "src/main/java/com/example/"
            + project_name.lower(),

            "src/main/java/com/example/"
            + project_name.lower()
            + "/controller",

            "src/main/java/com/example/"
            + project_name.lower()
            + "/service",

            "src/main/java/com/example/"
            + project_name.lower()
            + "/repository",

            "src/main/java/com/example/"
            + project_name.lower()
            + "/model",

            "src/main/java/com/example/"
            + project_name.lower()
            + "/dto",

            "src/main/java/com/example/"
            + project_name.lower()
            + "/mapper",

            "src/main/java/com/example/"
            + project_name.lower()
            + "/exception",

            "src/main/java/com/example/"
            + project_name.lower()
            + "/config",

            # Resources
            "src/main/resources",

            # Tests
            "src/test/java/com/example/"
            + project_name.lower(),

            "src/test/java/com/example/"
            + project_name.lower()
            + "/integration"
        ]

        for directory in directories:

            Path(
                os.path.join(
                    project_path,
                    directory
                )
            ).mkdir(
                parents=True,
                exist_ok=True
            )

        self.create_pom(
            project_path,
            project_name
        )

        self.create_application_yml(
            project_path
        )

        self.create_main_class(
            project_path,
            project_name
        )

        return project_path

    def create_pom(
            self,
            project_path,
            project_name
    ):

        pom_content = f"""
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="
         http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">

    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>
            org.springframework.boot
        </groupId>

        <artifactId>
            spring-boot-starter-parent
        </artifactId>

        <version>
            3.5.3
        </version>

        <relativePath/>
    </parent>

    <groupId>
        com.example
    </groupId>

    <artifactId>
        {project_name.lower()}
    </artifactId>

    <version>
        1.0.0
    </version>

    <name>
        {project_name}
    </name>

    <properties>
        <java.version>
            21
        </java.version>
    </properties>

    <dependencies>

        <dependency>
            <groupId>
                org.springframework.boot
            </groupId>

            <artifactId>
                spring-boot-starter-web
            </artifactId>
        </dependency>

        <dependency>
            <groupId>
                org.springframework.boot
            </groupId>

            <artifactId>
                spring-boot-starter-data-jpa
            </artifactId>
        </dependency>

        <dependency>
            <groupId>
                org.springframework.boot
            </groupId>

            <artifactId>
                spring-boot-starter-validation
            </artifactId>
        </dependency>

        <dependency>
            <groupId>
                org.springdoc
            </groupId>

            <artifactId>
                springdoc-openapi-starter-webmvc-ui
            </artifactId>

            <version>
                2.3.0
            </version>
        </dependency>

        <dependency>
            <groupId>
                org.projectlombok
            </groupId>

            <artifactId>
                lombok
            </artifactId>

            <optional>
                true
            </optional>
        </dependency>

        <dependency>
            <groupId>
                org.mapstruct
            </groupId>

            <artifactId>
                mapstruct
            </artifactId>

            <version>
                1.5.5.Final
            </version>
        </dependency>

        <dependency>
            <groupId>
                org.springframework.boot
            </groupId>

            <artifactId>
                spring-boot-starter-test
            </artifactId>

            <scope>
                test
            </scope>
        </dependency>

    </dependencies>

    <build>

        <plugins>

            <plugin>
                <groupId>
                    org.springframework.boot
                </groupId>

                <artifactId>
                    spring-boot-maven-plugin
                </artifactId>
            </plugin>

        </plugins>

    </build>

</project>
"""

        pom_path = os.path.join(
            project_path,
            "pom.xml"
        )

        with open(
                pom_path,
                "w",
                encoding="utf-8"
        ) as file:

            file.write(
                pom_content
            )

    def create_application_yml(
            self,
            project_path
    ):

        yml_content = """
spring:
  application:
    name: generated-service

server:
  port: 8080
"""

        yml_path = os.path.join(
            project_path,
            "src/main/resources/application.yml"
        )

        with open(
                yml_path,
                "w",
                encoding="utf-8"
        ) as file:

            file.write(
                yml_content
            )

    def create_main_class(
            self,
            project_path,
            project_name
    ):

        package_name = (
            project_name.lower()
        )

        class_name = (
            f"{project_name}"
            "Application"
        )

        content = f"""
package com.example.{package_name};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class {class_name} {{

    public static void main(
            String[] args
    ) {{

        SpringApplication.run(
            {class_name}.class,
            args
        );
    }}
}}
"""

        main_path = os.path.join(
            project_path,
            "src/main/java/com/example",
            package_name,
            f"{class_name}.java"
        )

        with open(
                main_path,
                "w",
                encoding="utf-8"
        ) as file:

            file.write(
                content
            )