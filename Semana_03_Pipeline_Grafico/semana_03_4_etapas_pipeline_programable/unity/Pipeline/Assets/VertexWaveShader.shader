Shader "Custom/VertexWaveShader"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Amplitude ("Wave Amplitude", Float) = 0.2
        _Frequency ("Wave Frequency", Float) = 2.0
        _Speed ("Wave Speed", Float) = 2.0
        _ColorA ("Gradient Color A", Color) = (0,0.5,1,1)
        _ColorB ("Gradient Color B", Color) = (1,0.5,0,1)
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" }

        Pass
        {
            CGPROGRAM

            #pragma vertex vert
            #pragma fragment frag

            #include "UnityCG.cginc"

            sampler2D _MainTex;

            float _Amplitude;
            float _Frequency;
            float _Speed;

            float4 _ColorA;
            float4 _ColorB;

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
                float3 normal : NORMAL;
            };

            struct v2f
            {
                float4 position : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 normal : TEXCOORD1;
                float3 worldPos : TEXCOORD2;
            };

            v2f vert (appdata v)
            {
                v2f o;

                float4 worldPos = mul(unity_ObjectToWorld, v.vertex);

                // Onda sinusoidal
                worldPos.y += sin(worldPos.x * _Frequency + _Time.y * _Speed) * _Amplitude;

                o.position = mul(UNITY_MATRIX_VP, worldPos);

                o.uv = v.uv;

                o.normal = mul((float3x3)unity_ObjectToWorld, v.normal);

                o.worldPos = worldPos.xyz;

                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                // NORMAL
                float3 N = normalize(i.normal);

                // DIRECCION DE LUZ
                float3 L = normalize(_WorldSpaceLightPos0.xyz);

                // ILUMINACION LAMBERT
                float lambert = max(dot(N, L), 0);

                // TEXTURA
                fixed4 tex = tex2D(_MainTex, i.uv);

                // GRADIENTE POR ALTURA
                float gradient = i.worldPos.y * 0.5 + 0.5;
                float4 gradColor = lerp(_ColorA, _ColorB, gradient);

                // PATTERN PROCEDURAL (grid)
                float gridX = frac(i.uv.x * 10);
                float gridY = frac(i.uv.y * 10);

                float gridLine = step(0.95, gridX) + step(0.95, gridY);

                float pattern = gridLine * 0.2;

                // COLOR FINAL
                fixed4 finalColor = tex * gradColor * lambert;

                finalColor.rgb += pattern;

                return finalColor;
            }       

            ENDCG
        }
    }
}